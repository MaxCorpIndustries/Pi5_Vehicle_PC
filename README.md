This repo contains the code meant for the custom dash screen meant for the 04 civic. 

This system should include the following features as the MVP:
- Working multi camera recording (similar to how a tesla has POV shots from the self driving cameras around the vehicle)
- Working statistics information from the EV Hybrid system and the ICE engine (maybe via speeduino configuration)
- Working screen output of the camera system
- Working aux or bluetooth integration with the phone 

## DEMO Gif
![alt text](https://github.com/MaxCorpIndustries/Pi5_Vehicle_PC/blob/main/CarPC_UI_Alpha1.gif)

## Planned Cameras and Locations

| CAM # | Camera Comms | Camera Make   | Video Specs        | Vehicle Location                                  |
|------:|--------------|---------------|--------------------|--------------------------------------------------|
| 1     | RTSP PoE     | RLC-510A      | 2304×1296 @ 30 FPS | Left outboard camera, facing rear of vehicle     |
| 2     | RTSP PoE     | RLC-510A      | 2304×1296 @ 30 FPS | Right outboard camera, facing rear of vehicle    |
| 3     | RTSP PoE     | RLC-510A      | 2304×1296 @ 30 FPS | Rear-facing camera                               |
| 4     | RTSP PoE     | Unknown       | ~1080p @ 30 FPS    | Front bumper camera                              |
| 5     | USB 3.0      | Logitech BRIO | ~1080p @ 30 FPS    | Under-mirror camera, facing front                |
| 6     | RTSP PoE     | Unknown       | ~1080p @ 30 FPS    | ClusterCam                                      |


 These streams run simultaneously at once, and should all be recorded as separate video files stored in a collected folder

