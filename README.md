# MediaMover

MediaMover是用于通过照片和视频的exif/meta信息里“相机型号”和拍摄日期筛选处理媒体文件。

mmover-et.py是依赖exiftool的版本，经测试速度远比用Pillow和ffmpeg实现的版本慢得多，因此不建议使用。