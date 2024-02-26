import time

### Create this to read into a databse of images ###

SAMPLE_IMAGES = [
    "https://static.wixstatic.com/media/e1234e_36641e0f2be447bea722377cd31945d3~mv2.jpg/v1/crop/x_254,y_168,w_972,h_937/fill/w_506,h_488,al_c,q_80,usm_0.66_1.00_0.01,enc_auto/IMG_20231215_134002.jpg",
]

def get_image(today_date):
    image_url = SAMPLE_IMAGES[0]
    return image_url