"""Offline QA only: call unchanged product functions and record state-machine traces."""
import hashlib,json,time,platform,sys
from pathlib import Path
import cv2
from PIL import Image,ImageDraw
from app.services.analyzer import analyze_video,ensure_model
from app.services.exercise_validation import validate_video_exercise
from app.services.exercise_profiles import ExerciseProfileLoader,RepDetector
from app.services.review_moments import rank_review_moments

root=Path('/workspace'); out=Path('/evidence'); out.mkdir(exist_ok=True)
sources={}
for rel in ['analyzer.py','exercise_validation.py','exercise_profiles.py','review_moments.py','biomechanics.py']:
    actual=Path('/app/app/services')/rel;expected=root/'app/services'/rel
    assert actual.read_bytes()==expected.read_bytes(),f'Image/source mismatch: {rel}'
    sources[rel]=hashlib.sha256(actual.read_bytes()).hexdigest()
for p in sorted(Path('/app/app/services/exercise_profiles').glob('*.json')):
    assert p.read_bytes()==(root/'app/services/exercise_profiles'/p.name).read_bytes()
    sources[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
(out/'frozen-environment.json').write_text(json.dumps({'python':sys.version,'platform':platform.platform(),'opencv':cv2.__version__,'model_sha256':hashlib.sha256(Path(ensure_model()).read_bytes()).hexdigest(),'sources_sha256':sources},indent=2),encoding='utf-8')

def trace(result,exercise,view):
    profile=ExerciseProfileLoader().load(exercise,view); detector=RepDetector(profile); transitions=[]
    for sample in result['timeline']:
        before=(detector.state,detector._last_valid_time,len(detector._repetitions))
        detector.consume(sample)
        after=(detector.state,detector._last_valid_time,len(detector._repetitions))
        if before[0]!=after[0] or (before[1] is not None and after[1] is not None and after[1]-before[1]>profile.noise['max_gap_s']):
            transitions.append({'time':sample['time_s'],'before':before[0],'after':after[0],'gap':None if before[1] is None else round(sample['time_s']-before[1],3),'signal':sample.get(profile.primary_signal),'pose_confidence':sample['pose_confidence'],'reps':after[2]})
    times=[x['time_s'] for x in result['timeline']]
    gaps=[round(b-a,3) for a,b in zip(times,times[1:])]
    signal=[x[profile.primary_signal] for x in result['timeline'] if x.get(profile.primary_signal) is not None]
    return {'profile':profile.id,'thresholds':profile.thresholds,'noise':profile.noise,'initial_state':profile.initial_state,'final_state':detector.state,'transitions':transitions,'valid_samples':len(times),'first_sample':times[0] if times else None,'last_sample':times[-1] if times else None,'gaps_over_limit':[g for g in gaps if g>profile.noise['max_gap_s']],'max_gap':max(gaps,default=0),'primary_signal':profile.primary_signal,'signal_min':min(signal,default=None),'signal_max':max(signal,default=None),'repetitions':detector._repetitions}

cases=[('clean-front','uploads/03e7f82b46b6.mp4','Clean','front'),('clean-side-diagnostic','uploads/03e7f82b46b6.mp4','Clean','side'),('press-negative-control','uploads/4275e6d44d08.mp4','Press','front'),('e2e-screencast','app/static/landing-demo.mp4','Sentadilla','side'),('low-resolution-demo','app/static/landing-analysis-example.mp4','Press','front')]
records=[]
for case,path,exercise,view in cases:
    source=root/path;record={'id':case,'path':path,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'exercise_selected':exercise,'view_selected':view,'observations_status':'DISABLED: no external provider called','observations':[]}
    start=time.perf_counter()
    try:
        record['preflight']=validate_video_exercise(str(source),exercise)
        record['preflight_seconds']=round(time.perf_counter()-start,3)
        result=analyze_video(str(source),str(out/case),exercise,view)
        result['preflight']=record['preflight'];record.update({'status':'COMPLETED','video':result['video'],'detected_reps':result['repetitions_detected'],'pose_quality':result['pose_quality'],'count_confidence':result['repetition_count_confidence'],'moments':rank_review_moments(result),'trace':trace(result,exercise,view)})
    except Exception as error:
        record.update(status='FAILED',error_type=type(error).__name__,error=str(error),detected_reps=None,moments=[])
    record['processing_seconds']=round(time.perf_counter()-start,3);records.append(record)
    (out/'measurements.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k not in {'trace','preflight','moments'}},ensure_ascii=False),flush=True)

old=json.loads((root/'.impeccable/review/athlete-persistence.json').read_text(encoding='utf-8'))['detail']['analysis_json']
(out/'e2e-persisted-trace.json').write_text(json.dumps(trace(old,'Sentadilla','side'),indent=2),encoding='utf-8')

for stem,path in [('clean','uploads/03e7f82b46b6.mp4'),('press','uploads/4275e6d44d08.mp4')]:
    cap=cv2.VideoCapture(str(root/path));duration=cap.get(cv2.CAP_PROP_FRAME_COUNT)/cap.get(cv2.CAP_PROP_FPS)
    timestamps=[i*.5 for i in range(int(duration/.5)+1)]
    for batch in range((len(timestamps)+19)//20):
        sheet=Image.new('RGB',(960,1400),'white');draw=ImageDraw.Draw(sheet)
        for j,t in enumerate(timestamps[batch*20:(batch+1)*20]):
            cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,frame=cap.read()
            if not ok:continue
            image=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));image.thumbnail((240,255));x=j%4*240;y=j//4*280;sheet.paste(image,(x,y));draw.text((x+4,y+258),f'{t:.2f}s',fill='black')
        sheet.save(out/f'{stem}-dense-{batch}.jpg')
    cap.release()
