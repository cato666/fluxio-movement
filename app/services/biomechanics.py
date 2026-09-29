import math
import numpy as np

def angle(a, b, c):
    """Angle ABC in degrees for 2D or 3D points."""
    a=np.array(a, dtype=float); b=np.array(b, dtype=float); c=np.array(c, dtype=float)
    ba=a-b; bc=c-b
    den=np.linalg.norm(ba)*np.linalg.norm(bc)
    if den == 0: return None
    cos=float(np.clip(np.dot(ba,bc)/den,-1,1))
    return round(math.degrees(math.acos(cos)),1)

def side_metrics(lm, side='left'):
    # MediaPipe indices
    idx = {'left': {'shoulder':11,'hip':23,'knee':25,'ankle':27},
           'right':{'shoulder':12,'hip':24,'knee':26,'ankle':28}}[side]
    pts={k:(lm[i][0],lm[i][1]) for k,i in idx.items()}
    return {
        'knee_angle': angle(pts['hip'], pts['knee'], pts['ankle']),
        'hip_angle': angle(pts['shoulder'], pts['hip'], pts['knee']),
        'trunk_from_vertical': round(abs(math.degrees(math.atan2(
            pts['shoulder'][0]-pts['hip'][0],
            -(pts['shoulder'][1]-pts['hip'][1])
        ))),1)
    }
