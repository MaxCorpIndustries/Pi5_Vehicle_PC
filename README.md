This repo contains the code meant for the custom dash screen meant for the 04 civic. 

This system should include the following features as the MVP:
- Working multi camera recording (similar to how a tesla has POV shots from the self driving cameras around the vehicle)
- Working statistics information from the EV Hybrid system and the ICE engine (maybe via speeduino configuration)
- Working screen output of the camera system
- Working aux or bluetooth integration with the phone 

The following are the planned cameras and their locations:
┌──────────┬───────────────┬───────────────┬───────────────────┬───────────────────────┐
│ CAM NUM  │ CAMERA COMS   | Camera Make   | vid Specs         | Vehicle location      |
├──────────┼───────────────┼───────────────┼───────────────────┼───────────────────────┤
│ 1        │ RTSP PoE      | RLC-510A      | 2304x1296 30Fps   | Left outboard camera, | 
│          |               |               |                   | facing rear of vehicle|
├──────────┼───────────────┼───────────────┼───────────────────┼───────────────────────┤
│ 2        | RTSP PoE      | RLC-510A      | 2304x1296 30Fps   | Right outboard camera,|  
│          |               |               |                   | facing rear of vehicle|
├──────────┼───────────────┼───────────────┼───────────────────┼───────────────────────┤
│ 3        | RTSP PoE      | RLC-510A      | 2304x1296 30Fps   | Rear facing camera.   |
├──────────┼───────────────┼───────────────┼───────────────────┼───────────────────────┤
│ 4        │ RTSP PoE      | unknown       | ~1080p 30Fps      | Front bumper camera   |
├──────────┼───────────────┼───────────────┼───────────────────┼───────────────────────┤
│ 5        │ USB 3.0       | Logitech BRIO | ~1080p 30Fps      | Under mirror cam      |
│          |               |               |                   | facing front          |
├──────────┼───────────────┼───────────────┼───────────────────┼───────────────────────┤
│ 6        │ RTSP PoE      | Unknown       | ~1080p 30Fps      | ClusterCam            |
└──────────┴───────────────┴───────────────┴───────────────────┴───────────────────────┘

 These streams run simultaneously at once, and should all be recorded as separate video files stored in a collected folder

