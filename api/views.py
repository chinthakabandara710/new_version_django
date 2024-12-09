import json
import base64
import qrcode
from io import BytesIO
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import pyrebase
from django.shortcuts import render
import uuid
import qrcode
import os
from PIL import Image
from io import BytesIO
import firebase_admin
from firebase_admin import credentials, storage
from firebase_admin import db
from decouple import config

firebase_config_path = config('FIREBASE_NewConfigurations')

# Load the Firebase configuration from the JSON file
with open(firebase_config_path, 'r') as file:
    newConfigurations = json.load(file)

# Initialize Firebase with the loaded configuration
firebase = pyrebase.initialize_app(newConfigurations)
database = firebase.database()
auth = firebase.auth()

user_token = ""

file_path = config('FIREBASE_CRED_PATH')
cred = credentials.Certificate(file_path)
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://restaurantapp-bbb0e-default-rtdb.asia-southeast1.firebasedatabase.app",
    "storageBucket": "restaurantapp-bbb0e.appspot.com"
})

def display_firebase_data(request):
    firebase_data = database.child("users").get()
    data = firebase_data.val() if firebase_data.each() else {}  
    
    return render(request, "firebase_data.html", {"data": data})

def register_view(request):
    return render(request, 'register.html')

def login_view(request):
    return render(request, 'login.html')

def add_assets_page(request):
    return render(request, 'add_assets.html')

@csrf_exempt
def register(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        firstName = data.get('firstName')
        lastName = data.get('lastName')
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type')
        is_admin = user_type == 'admin'

    try:
        user = auth.create_user_with_email_and_password(email, password)
        uid = user['localId']

        if is_admin:
            
            database.child("users").child(uid).set({"email": email, "isAdmin": True , "uid": uid , "firstName" : firstName,"lastName" : lastName})
        else:
            database.child("users").child(uid).set({"email": email, "isAdmin": False, "uid": uid , "firstName" : firstName,"lastName" : lastName})

        return JsonResponse({"status": "success", "message":"registered succcesfuly"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

@csrf_exempt
def login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

    try:
        user = auth.sign_in_with_email_and_password(email, password)
        user_info = auth.get_account_info(user['idToken'])
        uid = user_info['users'][0]['localId']
        
        user_data = database.child("users").child(uid).get().val()
        is_admin = user_data.get("isAdmin", False)

        uid = user_data.get("uid", '000')
        first_name = user_data.get("firstName", "FirstName")
        last_name = user_data.get("lastName", "LastName")

        return JsonResponse({
            "status": "success",
            "message": "Login successful",
            "isAdmin": is_admin,
            "uid":uid,
            "fullName": f"{first_name} {last_name}",
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
    
# def sign_in_user():
#     global user_token
#     if not user_token:
#         user = auth.sign_in_with_email_and_password("chinthaka@gmail.com", "123qwe")  # Use your real credentials
#         user_token = user['idToken']

def index(request):
    user_id = "001"
    try:
        data = {
            'age': database.child('users').child(user_id).child('age').get().val(),
            'email': database.child('users').child(user_id).child('email').get().val(),
            'fullname': database.child('users').child(user_id).child('fullname').get().val(),
            'id': database.child('users').child(user_id).child('id').get().val()
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def index_template(request):
    
    user_id = "001"       
    try:
        id = database.child('users').child(user_id).child('id').get(token=user_token).val()
        age = database.child('users').child(user_id).child('age').get(token=user_token).val()
        email = database.child('users').child(user_id).child('email').get(token=user_token).val()
        fullname = database.child('users').child(user_id).child('fullname').get(token=user_token).val()

        qr_data = f"Name: {fullname}, Email: {email}, Age: {age}, Id: {id}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        img_url = f"data:image/png;base64,{img_str}"

        context = {
            'id': id,
            'fullname': fullname,
            'email': email,
            'age': age,
            'qr_code': img_url  
        }
        
        return render(request, 'index.html', context)
    
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def update_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            asset_id = data.get("assetId")  
            user_id = data.get("userId")  
            if not asset_id:
                return JsonResponse({"status": "error", "message": "Asset ID is missing"}, status=400)

            new_status = "requesting"  
            
            # sign_in_user()  

            asset_ref = database.child('assets').child(asset_id) 
            print(f"Updating status for asset_id: {asset_id}")
            
            asset_ref.update({
                "assignedID": user_id,
                "status": new_status
            }, token=user_token)  

            return JsonResponse({"status": "success", "message": "Status updated to requesting"})
        except Exception as e:
            print(f"Error updating status: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

def get_all_users(request):
    try:
        all_users = database.child('users').get()
        if all_users.val():
            users_data = [user.val() for user in all_users.each()]
            return JsonResponse({"status": "success", "data": users_data})
        else:
            return JsonResponse({"status": "error", "message": "No users found in the collection"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
@csrf_exempt
def get_user_profile(request, uid):
    if request.method == 'GET':
        try:
            user_ref = db.reference(f"users/{uid}")
            user_data = user_ref.get()

            if user_data:
                return JsonResponse({"status": "success", "data": user_data})
            else:
                return JsonResponse({"status": "error", "message": "User not found."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method."})
    
# def get_all_assets(request):
#     try:
#         user = auth.sign_in_with_email_and_password("chinthaka@gmail.com", "123qwe") 
#         token = user['idToken']  
        
      
#         all_assets = database.child('assets').get(token=token) 
        
#         if all_assets.val():
#             assets_data = [{
#                 "assetId": asset_info.get('assetId'),
#                 "category": asset_info.get('category'),
#                 "name": asset_info.get('name'),
#                 "quantity": asset_info.get('quantity'),
#                 "status": asset_info.get('status'),
#             } for asset_info in all_assets.each()]

#             return JsonResponse({"status": "success", "data": assets_data})
#         else:
#             return JsonResponse({"status": "error", "message": "No assets found in the collection"}, status=404)

@csrf_exempt
def get_assets_with_assigned_id(request):
    user_id = request.GET.get('user_id')
    if not user_id:
        return JsonResponse({"status": "error", "message": "user_id parameter is missing"}, status=400)

    try:

        assets = database.child('assets').order_by_child('assignedID').equal_to(user_id).get()

        if not assets.each():
            print("No assets found.")
            return JsonResponse({"status": "error", "message": "No assets found with assignedID"}, status=404)

        assets_list = [asset.val() for asset in assets.each()]
        print(f"Assets found: {assets_list}")
        return JsonResponse({"status": "success", "data": assets_list}, status=200)

    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({"status": "error", "message": f"Error fetching assets: {str(e)}"}, status=400)


@csrf_exempt
def add_assets(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            category = data.get('category')
            location = data.get('location')
            date_of_purchase = data.get('date_of_purchase')
            quantity = data.get('quantity')
            image ='https://w7.pngwing.com/pngs/1010/184/png-transparent-power-supply-unit-power-converters-80-plus-atx-electric-power-computer-electronics-computer-electronic-device.png'


            if not all([name, category, location, date_of_purchase, quantity]):
                return JsonResponse({"status": "error", "message": "All fields are required (name, category, location, date_of_purchase, quantity)"}, status=400)

            asset_id = str(uuid.uuid4())

            # Create QR Code
            # qr_data = f"Asset ID: {asset_id}\nName: {name}\nCategory: {category}\nLocation: {location}\nQuantity: {quantity}\nDate of Purchase: {date_of_purchase}\nImage: {image}"
            qr_data = f"Asset ID: {asset_id}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)

            img = qr.make_image(fill='black', back_color='white')
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            buffered.seek(0)

            bucket = storage.bucket()  
            file_name = f"assets_qr/{asset_id}.png"
            blob = bucket.blob(file_name)
            blob.upload_from_file(buffered, content_type="image/png")
            blob.make_public()
            qr_url = blob.public_url  # Get public URL of the uploaded QR code

            database.child('assets').child(asset_id).set({
                'assetID': asset_id,
                'name': name,
                'category': category,
                'location': location,
                'date_of_purchase': date_of_purchase,
                'quantity': int(quantity),
                'qr_url': qr_url,
                'image':'https://w7.pngwing.com/pngs/1010/184/png-transparent-power-supply-unit-power-converters-80-plus-atx-electric-power-computer-electronics-computer-electronic-device.png'
            })

            return JsonResponse({"status": "success", "message": "Asset added successfully", "assetID": asset_id, "qr_url": qr_url}, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


def get_all_assets(request):
    user_id = "001"  
    try:
        assets = database.child('assets').get(token=user_token)

        if not assets.each():
            return JsonResponse({"status": "error", "message": "No assets found with assignedID"}, status=404)

        assets_list = [asset.val() for asset in assets.each()]
        return JsonResponse({"status": "success", "data": assets_list}, status=200)

    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({"status": "error", "message": f"Error fetching assets: {str(e)}"}, status=400)
    
@csrf_exempt
def approve_assets(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            asset_id = data.get("assetId")  
            if not asset_id:
                return JsonResponse({"status": "error", "message": "Asset ID is missing"}, status=400)

            new_status = "Approved"  
            
            # sign_in_user()  

            asset_ref = database.child('assets').child(asset_id) 

            print(f"Updating status for asset_id: {asset_id}")
            
            asset_ref.update({
                "status": new_status
            }, token=user_token)  

            return JsonResponse({"status": "success", "message": "Status updated to requesting"})
        except Exception as e:
            print(f"Error updating status: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
    
# ********************
@csrf_exempt
def add_category(request):
    if request.method == 'POST':
        # Parse JSON data from the request body
        data = json.loads(request.body)
        category_name = data.get('category_name')
        description = data.get('description')
        created_by = data.get('created_by')
        is_active = data.get('is_active', True)  # Default to True if not provided
        created_at = data.get('created_at')  # Ensure client sends a timestamp or date string

        # Basic validation
        if not category_name or not description or not created_by:
            return JsonResponse({"status": "error", "message": "Missing required fields."}, status=400)

        try:
            # Generate unique ID for the category
            category_id = database.generate_key()

            # Add category details to Firebase
            database.child("categories").child(category_id).set({
                "category_name": category_name,
                "description": description,
                "created_by": created_by,
                "is_active": is_active,
                "created_at": created_at
            })

            return JsonResponse({"status": "success", "message": "Category added successfully.", "category_id": category_id})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid HTTP method."}, status=405)

@csrf_exempt
def add_subcategory(request):
    if request.method == 'POST':
        # Parse JSON data from the request body
        data = json.loads(request.body)
        subcategory_name = data.get('subcategory_name')
        description = data.get('description')
        parent_category_id = data.get('parent_category_id')  # ID of the category this subcategory belongs to
        created_by = data.get('created_by')
        is_active = data.get('is_active', True)  # Default to True if not provided
        created_at = data.get('created_at')  # Ensure client sends a timestamp or date string

        # Basic validation
        if not subcategory_name or not description or not parent_category_id or not created_by:
            return JsonResponse({"status": "error", "message": "Missing required fields."}, status=400)

        try:
            # Check if parent category exists
            category_exists = database.child("categories").child(parent_category_id).get().val()
            if not category_exists:
                return JsonResponse({"status": "error", "message": "Parent category does not exist."}, status=404)

            # Generate unique ID for the subcategory
            subcategory_id = database.generate_key()

            # Add subcategory details under the parent category
            database.child("categories").child(parent_category_id).child("subcategories").child(subcategory_id).set({
                "subcategory_name": subcategory_name,
                "description": description,
                "created_by": created_by,
                "is_active": is_active,
                "created_at": created_at
            })

            return JsonResponse({"status": "success", "message": "Subcategory added successfully.", "subcategory_id": subcategory_id})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid HTTP method."}, status=405)



# def get_categories(request):
#     try:
#         # Fetch all categories from Firebase
#         categories = database.child("categories").get().val()

#         if not categories:
#             return JsonResponse({"status": "success", "message": "No categories found.", "data": []})

#         return JsonResponse({"status": "success", "data": categories})

#     except Exception as e:
#         return JsonResponse({"status": "error", "message": str(e)}, status=500)

from django.http import JsonResponse

def get_categories(request):
    try:
        # Get the search query from the request (category_name entered by the user)
        category_name = request.GET.get('category_name', '').strip()

        # Fetch all categories from Firebase
        categories = database.child("categories").get().val()

        if not categories:
            return JsonResponse({"status": "success", "message": "No categories found.", "data": []})

        # Filter categories by the search query
        filtered_categories = {
            key: value
            for key, value in categories.items()
            if category_name.lower() in value.get("category_name", "").lower()
        }

        if not filtered_categories:
            return JsonResponse({"status": "success", "message": "No matching categories found.", "data": []})

        return JsonResponse({"status": "success", "data": filtered_categories})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)



def get_subcategories(request, category_id):
    try:
        # Fetch the category by ID
        category = database.child("categories").child(category_id).get().val()

        if not category:
            return JsonResponse({"status": "error", "message": "Category not found."}, status=404)

        # Fetch subcategories under the specified category
        subcategories = category.get("subcategories", {})

        return JsonResponse({"status": "success", "data": subcategories})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
