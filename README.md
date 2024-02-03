# MMover = MediaMover

### What is MMover
MMover is a tool to copy/move pictures and videos according to camera model and creation date information in the exif/metadata of the file.
MediaMover是用于通过照片和视频的exif/meta信息里“相机型号”和拍摄日期筛选处理媒体文件。

mmover-et.py depends on 3rd-party 'exiftool'. It's tested to be much slower than the version use 'Pillow' and 'ffmpeg' to extract exif/metadata from files, hence it's deprecated. I just leave it here for study/reference.
mmover-et.py是依赖exiftool的版本，经测试速度远比用Pillow和ffmpeg实现的版本慢得多，因此不建议使用。 

### Dependencies
* pillow
* pillow-heif
* ffmpeg-python
* ffmpeg (external programs package required for runtime, e.g. when you run the program with `python mmover.py -c "iPhone 15" copy image "source_path" "dest_path"`)

### Build and Packaging
Install PyInstaller, and run this in the program file directory:
> pyinstaller mmover.spec
