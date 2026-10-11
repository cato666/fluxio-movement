"""Administrative accounts and durable, serialized monthly quotas."""
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID
import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from .database import get_session
from .models import User, Athlete, Coach, AdminSetting, AdminAudit, PlanInteraction
from .services.auth import hash_password

OPERATIONS = ('ANALYZE', 'INTERPRET', 'TRANSCRIBE')
DEFAULT_POLICIES = {plan: {'monthly_limit': limit, 'enabled_operations': list(OPERATIONS)}
                    for plan, limit in [('FREE', 10), ('PAID', 200)]}


def policies(session):
    row = session.get(AdminSetting, 'plans')
    return row.value if row else DEFAULT_POLICIES


def usage(session, user):
    start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    count = session.scalar(select(func.count()).select_from(PlanInteraction).where(
        PlanInteraction.user_id == user.id, PlanInteraction.created_at >= start, PlanInteraction.reservation_state != 'RELEASED'))
    policy = policies(session)[user.plan]
    return {'plan': user.plan, 'used': count, 'monthly_limit': policy['monthly_limit'],
            'remaining': max(0, policy['monthly_limit'] - count), 'enabled_operations': policy['enabled_operations'],
            'period_start': start}


def consume(session, user_id, operation, request_key=None):
    from .services.consumption_limits import reserve
    identifier = reserve(session, user_id, operation, request_key=request_key)
    session.info['consumption_reservation'] = identifier
    session.commit()
    return identifier


class AccountPayload(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    username: str = Field(min_length=3, max_length=40)
    email: str | None = Field(default=None, max_length=254)
    role: Literal['ATHLETE', 'COACH', 'SYSTEM_ADMIN']
    plan: Literal['FREE', 'PAID'] = 'FREE'
    is_active: bool = True
    password: str | None = Field(default=None, min_length=8, max_length=200)


class PolicyPayload(BaseModel):
    monthly_limit: int = Field(ge=0, le=1000000)
    enabled_operations: list[Literal['ANALYZE', 'INTERPRET', 'TRANSCRIBE']]


class OrganizationPayload(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    contact_email: str = Field(default='', max_length=254)


def fields(user):
    return {key: getattr(user, key) for key in ('id', 'name', 'email', 'role', 'plan', 'is_active', 'last_login_at', 'created_at')} | {'username': user.demo_key}


def audit(session, actor, action, target, changes):
    session.add(AdminAudit(actor_id=actor.id, action=action, target=str(target), changes=changes))


def router(require_admin, authenticated):
    routes = APIRouter()

    @routes.get('/api/account/plan')
    def account_plan(user=Depends(authenticated), session=Depends(get_session)):
        return usage(session, user)

    @routes.get('/api/admin/users')
    def users(_user=Depends(require_admin), session=Depends(get_session)):
        return {'items': [fields(user) | {'usage': usage(session, user)} for user in session.scalars(select(User).order_by(User.name))]}

    def save(payload, actor, session, identifier=None):
        # Serialize administrator changes to protect the last active administrator.
        session.execute(select(User.id).where(User.role == 'SYSTEM_ADMIN').order_by(User.id).with_for_update()).all()
        user = session.scalar(select(User).where(User.id == identifier).with_for_update()) if identifier else None
        if identifier and user is None:
            raise HTTPException(404, 'Usuario no encontrado')
        data = payload.model_dump(exclude={'password'})
        data['name'] = data['name'].strip()
        username = data.pop('username').strip().casefold()
        if not data['name'] or not re.fullmatch(r'[a-z0-9._-]{3,40}', username):
            raise HTTPException(422, 'Indica un nombre y un usuario válido (letras, números, punto o guion)')
        email = (data['email'] or '').strip().casefold() or None
        if email and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            raise HTTPException(422, 'Correo inválido')
        data['email'], data['demo_key'] = email, username
        if user and user.role != data['role']:
            raise HTTPException(409, 'El rol de una cuenta existente conserva sus relaciones; crea una cuenta con el nuevo rol')
        if user and user.role == 'SYSTEM_ADMIN' and not data['is_active']:
            others = session.scalar(select(func.count()).select_from(User).where(User.role == 'SYSTEM_ADMIN', User.is_active.is_(True), User.id != user.id))
            if not others:
                raise HTTPException(409, 'Debe existir al menos un administrador activo')
        before = {key: getattr(user, key) for key in data} if user else {}
        if not user:
            if not payload.password:
                raise HTTPException(422, 'Indica una contraseña inicial de al menos 8 caracteres')
            user = User(**data, is_internal=data['role'] == 'SYSTEM_ADMIN')
            session.add(user)
        else:
            for key, value in data.items():
                setattr(user, key, value)
        if payload.password:
            user.password_hash = hash_password(payload.password)
        try:
            session.flush()
            if not identifier and user.role == 'ATHLETE':
                session.add(Athlete(user_id=user.id))
            if not identifier and user.role == 'COACH':
                session.add(Coach(user_id=user.id, specialty='General'))
            changes = {key: {'before': before.get(key), 'after': value} for key, value in data.items() if before.get(key) != value}
            if payload.password:
                changes['password_reset'] = True
            if before.get('is_active') and not user.is_active and user.role == 'ATHLETE':
                # Revoke channel state in the same transaction as deactivation.
                from .whatsapp.identity import IdentityResolver
                IdentityResolver(session, None).revoke(user.id)
            audit(session, actor, 'USER_UPDATED' if identifier else 'USER_CREATED', user.id, changes)
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(409, 'El usuario o correo ya está registrado')
        return fields(user)

    @routes.post('/api/admin/users', status_code=201)
    def create(payload: AccountPayload, actor=Depends(require_admin), session=Depends(get_session)):
        return save(payload, actor, session)

    @routes.put('/api/admin/users/{identifier}')
    def update(identifier: UUID, payload: AccountPayload, actor=Depends(require_admin), session=Depends(get_session)):
        return save(payload, actor, session, identifier)

    @routes.get('/api/admin/settings')
    def settings(_user=Depends(require_admin), session=Depends(get_session)):
        organization = session.get(AdminSetting, 'organization')
        consumption = session.get(AdminSetting, 'consumption_limits')
        return {'consumption_limits': consumption.value if consumption else None, 'plans': policies(session), 'organization': organization.value if organization else {'name': 'Fluxio Movement', 'contact_email': ''},
                'roles': {'SYSTEM_ADMIN': 'Usuarios, planes, configuración y auditoría', 'COACH': 'Revisiones y registro de atletas', 'ATHLETE': 'Entrenamientos y análisis propios'}}

    def set_setting(session, actor, key, value):
        row = session.get(AdminSetting, key)
        before = row.value if row else None
        if row:
            row.value = value
        else:
            session.add(AdminSetting(key=key, value=value))
        audit(session, actor, 'SETTINGS_UPDATED', key, {'before': before, 'after': value})
        session.commit()
        return {'ok': True}

    @routes.put('/api/admin/plans')
    def plans(payload: dict[Literal['FREE', 'PAID'], PolicyPayload], actor=Depends(require_admin), session=Depends(get_session)):
        if set(payload) != {'FREE', 'PAID'}:
            raise HTTPException(422, 'Configura ambos planes')
        return set_setting(session, actor, 'plans', {key: value.model_dump() for key, value in payload.items()})

    @routes.put('/api/admin/consumption-limits')
    def consumption_limits(payload: dict, actor=Depends(require_admin), session=Depends(get_session)):
        from .services.consumption_limits import configuration, DEFAULTS, VIDEO_COSTS, LOCK
        from sqlalchemy import text
        allowed = set(DEFAULTS) | set(VIDEO_COSTS) | {'PILOT_START'}
        if set(payload) != allowed:
            raise HTTPException(422, 'Configura todos los límites y costos; no se admiten campos adicionales')
        configuration(session, 'ANALYZE', overrides=payload)
        session.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': LOCK})
        window = session.get(AdminSetting, 'consumption_window')
        if window and window.value['start'] != configuration(session, overrides=payload)['PILOT_START'].isoformat():
            raise HTTPException(409, 'El inicio del piloto no puede cambiar después de reservar consumo')
        return set_setting(session, actor, 'consumption_limits', payload)

    @routes.put('/api/admin/organization')
    def organization(payload: OrganizationPayload, actor=Depends(require_admin), session=Depends(get_session)):
        if not payload.name.strip():
            raise HTTPException(422, 'Indica el nombre de la organización')
        if payload.contact_email and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', payload.contact_email):
            raise HTTPException(422, 'Correo de contacto inválido')
        return set_setting(session, actor, 'organization', payload.model_dump())

    @routes.get('/api/admin/audit')
    def history(_user=Depends(require_admin), session=Depends(get_session)):
        rows = session.execute(select(AdminAudit, User.name).join(User, User.id == AdminAudit.actor_id).order_by(AdminAudit.created_at.desc()).limit(100))
        return {'items': [{'actor': name, 'action': row.action, 'target': row.target, 'changes': row.changes, 'created_at': row.created_at} for row, name in rows]}

    return routes
