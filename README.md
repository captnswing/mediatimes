To use this you need

    brew install exiftool git fdupes pyenv
    
    pyenv install 3.8.2
    pyenv virtualenv 3.8.2 mediatimes
    git clone git@github.com:captnswing/mediatimes.git
    cd mediatimes
    pyenv local mediatimes
    pip install -r requirements.txt   

now you can
     
    exiftool -@ exif.args <directory>
    exiftool -@ exif_args.cfg -ext .gif -ext .heic -ext .jpeg -ext .jpg -ext .png '/Volumes/Photos/Google Photos'  2>errors_images.txt
    exiftool -@ exif_args.cfg -ext .3gp -ext .avi -ext .mov -ext .mp4 -ext .mpg '/Volumes/Photos/Google Photos' 2>errors_videos.txt
    
* https://exiftool.org/exiftool_pod.html
* https://exiftool.org/faq.html
* https://www.google.com/search?client=firefox-b-d&q=exiftool+google+takeout
* https://legault.me/post/correctly-migrate-away-from-google-photos-to-icloud
    
