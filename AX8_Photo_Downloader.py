#imports
import os, requests, json, time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

#function to find index of dictionary within list of desired key 
def find_json_index(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return "ERROR"

#return data value from list using correct index
def find_json_values(lst,idx):
    if len(lst) >= idx:
        return lst[idx]
    return "ERROR"

def check_for_csv(filelocation):
    #if file exists then open it
    if os.path.isfile(filelocation):
        file= open(filelocation, "a")
    #if file does not exist then create it
    else:
        file= open(filelocation, "w")
    #if file is empty/just created then insert headers
    if os.stat(filelocation).st_size == 0:
        file.write("Date,Temperature ,Relative Humidity\n")

#save data from web api json to local csv file for later reference if needed
def save_to_csv(filelocation,AirTemp,RelHum):
    file= open(filelocation,"a")
    file.write(now.strftime("%m/%d/%Y %H:%M") +","+str(AirTemp)+","+str(RelHum)+"\n")
    file.close()

#creates folder holding all images taken that day 
def create_camera_folder(folder):
    folder_exists = os.path.exists(folder)
    if not folder_exists:
        os.makedirs(folder)
    else:
        print("Folder Exists")

#connect & login to camera
def connect_to_camera(cam_ip,image_directory,AirTC,RelHum):
        options = webdriver.ChromeOptions()
        #options.add_argument('headless')
        options.add_experimental_option("prefs", {
          "profile.managed_default_content_settings.images": 2,
          "profile.managed_default_content_settings.popups":2,
          "profile.default_content_setting_values.notifications":2,
          "download.default_directory": image_directory,
          "download.prompt_for_download": False,
          "download.directory_upgrade": True,
          "safebrowsing.enabled": True
        })

        #Open up Chrome Webdriver
        driver = webdriver.Chrome(options=options)
        #print ('Loading Chrome')
        driver.implicitly_wait(10)
        #Load camera website via IP
        driver.get(cam_ip)
        #Log into the camera
        username = driver.find_element_by_name("user_name").send_keys('admin')
        password = driver.find_element_by_name("user_password").send_keys("admin")
        login = driver.find_element_by_id("button-login").click()
        print ('Webpage ', cam_ip, ' loaded')
        print ('Logged in')

        #Change Values to CR1000x Values
        parameters_menu = driver.find_element_by_id('button-global-parameters').click()
        print('Menu Clicked')
        
        time.sleep(3)
        
        #CTRL + A to select and replace values
        Reflected_Temp = driver.find_element_by_class_name("global-ambient-temp")
        Reflected_Temp.send_keys(Keys.CONTROL + "a")
        Reflected_Temp.send_keys(AirTC)
        #print ('Reflected Temperature Values Changed')
        Atmospheric_Temp = driver.find_element_by_class_name("global-atmospheric-temp")
        Atmospheric_Temp.send_keys(Keys.CONTROL + "a")
        Atmospheric_Temp.send_keys(AirTC)
        #print ('Atmospheric Temperature Values Changed')
        Relative_Humidity = driver.find_element_by_class_name("global-relative-humidity")
        Relative_Humidity.send_keys(Keys.CONTROL + "a")
        Relative_Humidity.send_keys(RelHum)
        Relative_Humidity.send_keys(Keys.ENTER)
        #print('Humidity Values Changed')
        
        #close window of parameters to confirm change
        parameters_menu = driver.find_element_by_id('button-global-parameters').click()
        
        time.sleep(3)

        #Caputre Photo
        CapturePhoto = driver.find_element_by_id('button-save-image').click()
        print ('Photo has been taken')

        time.sleep(3)

        #Access Storage page of photos 
        storagePage = driver.find_element_by_link_text('STORAGE').click()
        print ('Storage Page Accessed')

        #Start Downloading photos
        link = driver.find_element_by_css_selector('.button.button-storage-save').click()
        print ('Photo Downloaded')

        driver.quit()

        #functions to ensure all images are properly named
        save_rename_images(image_directory)
        #function to ensure no duplicates have been downloaded and kept
        remove_duplicate_images(image_directory)

def save_rename_images(image_directory):
    #renames and adds Camera to front of filename
    for root, dirs, files in os.walk(image_directory):
        if not files:
            continue
        #prefix = os.path.basename(root)
        #splits string by folders and returns current camera we are checking
        prefix = root.split("\\\\")[-2]

        for f in files:
            if prefix in f:
                #print("Contains it")
                continue
            else:
                if f.endswith(".jpg"):
                    os.rename(os.path.join(root, f), os.path.join(root, "{}_{}".format(prefix,f)))   

def remove_duplicate_images(image_directory):
    #Removes all Duplicate Photos
    file_path = image_directory
    file_list = os.listdir(file_path)
    for file_name in file_list:
        if " (1)" not in file_name:
            continue
        original_file_name = file_name.replace(' (1)', '')
        if not os.path.exists(os.path.join(file_path, original_file_name)):
            continue  # do not remove files which have no original
        os.remove(os.path.join(file_path, file_name)) 

if __name__ == "__main__":
    #current time 
    now = datetime.now() 

    print("change --prefix-- VARIABLE based on windows/linux folders")
    print("change DIRECTORIES")

    #change this to correct folder where csv file is desired
    csv_file = r"Camera_Temp_Humidity_Values.csv"
    #folders holding images for each camera
    camera1_directory = r"Camera1\\" + now.strftime("%m_%d_%Y")
    camera2_directory = r"Camera2\\" + now.strftime("%m_%d_%Y")
    camera3_directory = r"Camera3\\" + now.strftime("%m_%d_%Y")

    #web api call to CR1000x to query Public datatable and recent most-recent data in json format
    #info on API
    #https://help.campbellsci.com/crbasic/cr1000x/#Info/webserverapicommands1.htm#kanchor360
    #dataquery example
    #https://help.campbellsci.com/crbasic/cr1000x/Content/Info/dataqueryexamples1.htm
    response = requests.get("http://IP ADDRESS HERE/?command=dataquery&uri=dl:Public&format=json&mode=most-recent").json()
    #find index of values needed
    AirTC_index = find_json_index(response['head']['fields'],'name','AirTC')
    RH_index = find_json_index(response['head']['fields'],'name','RH')
    #find correct values based on indices above
    AirTC_value = find_json_values(response['data'][0]['vals'], AirTC_index)
    RH_value = find_json_values(response['data'][0]['vals'], RH_index)

    #create csv file if does not exists
    check_for_csv(csv_file)
    #save values to csv file
    save_to_csv(csv_file,AirTC_value,RH_value)

    #create new daily directory for each camera if does not exist
    create_camera_folder(camera1_directory)
    create_camera_folder(camera2_directory)
    create_camera_folder(camera3_directory)

    #camera IPs to change Temp/RelHum values then capture image
    camera1_IP = "IP ADDRESS HERE"
    camera2_IP = "IP ADDRESS HERE"
    camera3_IP = "IP ADDRESS HERE"

    #connect to camera, change values, capture image, save image, rename image, delete any duplicates IF download
    #connect_to_camera(camera1_IP,camera1_directory,AirTC_value,RH_value)
    #connect_to_camera(camera2_IP,camera1_directory,AirTC_value,RH_value)
    #connect_to_camera(camera3_IP,camera1_directory,AirTC_value,RH_value)

    #functions to ensure all images are properly named
    save_rename_images(camera1_directory)
    #function to ensure no duplicates have been downloaded and kept
    remove_duplicate_images(camera1_directory)