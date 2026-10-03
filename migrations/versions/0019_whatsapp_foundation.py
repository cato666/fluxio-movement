"""Add verified WhatsApp identity and durable queues; no backfill."""
from alembic import op

revision = "0019_whatsapp_foundation"
down_revision = "0018_training_ai_usage"
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE TABLE whatsapp_peers (\n\tphone_hash VARCHAR(64) NOT NULL, \n\twindow_start TIMESTAMP WITH TIME ZONE NOT NULL, \n\tattempts INTEGER DEFAULT '0' NOT NULL, \n\tlast_message_at TIMESTAMP WITH TIME ZONE, \n\tPRIMARY KEY (phone_hash)\n)")
    op.execute('CREATE TABLE athlete_identity (\n\tid UUID NOT NULL, \n\tathlete_id UUID NOT NULL, \n\tphone_encrypted TEXT NOT NULL, \n\tphone_hash VARCHAR(64) NOT NULL, \n\tkey_version VARCHAR(32) NOT NULL, \n\tverified_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\trevoked_at TIMESTAMP WITH TIME ZONE, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(athlete_id) REFERENCES athletes (user_id)\n)')
    op.execute('CREATE INDEX ix_athlete_identity_athlete_id ON athlete_identity (athlete_id)')
    op.execute('CREATE UNIQUE INDEX uq_identity_active_athlete ON athlete_identity (athlete_id) WHERE revoked_at IS NULL')
    op.execute('CREATE UNIQUE INDEX uq_identity_active_phone ON athlete_identity (phone_hash) WHERE revoked_at IS NULL')
    op.execute("CREATE TABLE conversation_state (\n\tathlete_id UUID NOT NULL, \n\tchannel VARCHAR(16) NOT NULL, \n\tstate VARCHAR(32) NOT NULL, \n\tpending_action VARCHAR(100), \n\tpayload_minimized TEXT, \n\tkey_version VARCHAR(32) NOT NULL, \n\texpires_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tversion INTEGER DEFAULT '0' NOT NULL, \n\tPRIMARY KEY (athlete_id, channel), \n\tFOREIGN KEY(athlete_id) REFERENCES athletes (user_id)\n)")
    op.execute("CREATE TABLE whatsapp_inbox (\n\tid UUID NOT NULL, \n\tprovider VARCHAR(16) NOT NULL, \n\tprovider_message_id VARCHAR(240) NOT NULL, \n\tmessage_type VARCHAR(24) NOT NULL, \n\tevent VARCHAR(24) NOT NULL, \n\tpeer_hash VARCHAR(64), \n\tathlete_id UUID, \n\tpayload_encrypted TEXT, \n\tkey_version VARCHAR(32) NOT NULL, \n\tstate VARCHAR(24) DEFAULT 'PENDING' NOT NULL, \n\tattempts INTEGER DEFAULT '0' NOT NULL, \n\tlease_until TIMESTAMP WITH TIME ZONE, \n\tnext_attempt_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\thappened_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\texpires_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\terror_code VARCHAR(64), \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tprocessed_at TIMESTAMP WITH TIME ZONE, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_whatsapp_inbox_message UNIQUE (provider, provider_message_id), \n\tFOREIGN KEY(athlete_id) REFERENCES athletes (user_id)\n)")
    op.execute('CREATE INDEX ix_whatsapp_inbox_peer_hash ON whatsapp_inbox (peer_hash)')
    op.execute('CREATE INDEX ix_whatsapp_inbox_state ON whatsapp_inbox (state)')
    op.execute("CREATE TABLE whatsapp_link_challenges (\n\tid UUID NOT NULL, \n\tathlete_id UUID NOT NULL, \n\tcode_hash VARCHAR(64) NOT NULL, \n\tattempts INTEGER DEFAULT '0' NOT NULL, \n\texpires_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tconsumed_at TIMESTAMP WITH TIME ZONE, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(athlete_id) REFERENCES athletes (user_id), \n\tUNIQUE (code_hash)\n)")
    op.execute('CREATE INDEX ix_whatsapp_link_challenges_athlete_id ON whatsapp_link_challenges (athlete_id)')
    op.execute("CREATE TABLE whatsapp_outbox (\n\tid UUID NOT NULL, \n\tathlete_id UUID, \n\tdedupe_key VARCHAR(160) NOT NULL, \n\taction VARCHAR(32) NOT NULL, \n\tpayload_encrypted TEXT, \n\tkey_version VARCHAR(32) NOT NULL, \n\tprovider_message_id VARCHAR(240), \n\tattempts INTEGER DEFAULT '0' NOT NULL, \n\tnext_attempt_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tstate VARCHAR(24) DEFAULT 'PENDING' NOT NULL, \n\tlease_until TIMESTAMP WITH TIME ZONE, \n\terror_code VARCHAR(64), \n\texpires_at TIMESTAMP WITH TIME ZONE NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(athlete_id) REFERENCES athletes (user_id), \n\tUNIQUE (dedupe_key)\n)")
    op.execute('CREATE INDEX ix_whatsapp_outbox_athlete_id ON whatsapp_outbox (athlete_id)')
    op.execute('CREATE INDEX ix_whatsapp_outbox_provider_message_id ON whatsapp_outbox (provider_message_id)')
    op.execute('CREATE INDEX ix_whatsapp_outbox_state ON whatsapp_outbox (state)')
    op.execute('CREATE TABLE whatsapp_usage (\n\tid UUID NOT NULL, \n\tathlete_id UUID, \n\tevent_key VARCHAR(200) NOT NULL, \n\tcategory VARCHAR(32) NOT NULL, \n\tunits INTEGER NOT NULL, \n\tcost NUMERIC(18, 8), \n\tcurrency VARCHAR(3) NOT NULL, \n\tcreated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(athlete_id) REFERENCES athletes (user_id), \n\tUNIQUE (event_key)\n)')
    op.execute('CREATE INDEX ix_whatsapp_usage_athlete_id ON whatsapp_usage (athlete_id)')


def downgrade():
    op.drop_table('whatsapp_usage')
    op.drop_table('whatsapp_outbox')
    op.drop_table('whatsapp_link_challenges')
    op.drop_table('whatsapp_inbox')
    op.drop_table('conversation_state')
    op.drop_table('athlete_identity')
    op.drop_table('whatsapp_peers')
