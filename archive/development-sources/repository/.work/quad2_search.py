from quadrant_v2 import *
if __name__=='__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=3)as pool:
        for r in pool.map(trial,[(2,s)for s in range(900,960)]):
            if r:print(json.dumps(r),flush=True)
