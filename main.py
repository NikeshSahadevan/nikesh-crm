import json
FILE_NAME = "leads.json"

def load_leads():
    try:
        with open(FILE_NAME,"r") as file :
            return json.load(file)
    except FileNotFoundError :
        return[]

def save_leads(leads):
    with open(FILE_NAME,"w") as file:
        json.dump(leads,file,indent=4)

leads = load_leads()

while True :
    choice = input("\n1. Add Lead\n2. View Leads\n3. Search Lead\n4. Delete Lead\n5. Edit\n6. Exit\nEnter choice: ")
    if choice == '1' :
        name = input("Enter the Name : ")
        number = input("Enter the Mobile Number : ")
        lead = {
            "name" : name,
            "number" : number
        }

        leads.append(lead)
        save_leads(leads)
        print("Lead added Sucessfully1")
    elif choice == '2' :
        if not leads :
            print("No Leads Available")
        else :
            for lead in  leads:
                print(f"Name : {lead['name']}, Phone : {lead['number']}")

    elif choice == '3':
        search_name = input("Enter name to  search : ")
        found = False
        for lead in  leads:
            if search_name.lower() in  lead['name'].lower():
                print(f"Found : {lead['name']} - {lead['number']}")
                found = True

        if not  found:
            print("No  lead in name. Pleace Check.......")

    elif choice == '4':
        delete_name = input("Enter name to  Delete : ")
        found = False
        for lead in leads:
            if lead['name'].lower() == delete_name.lower():
                leads.remove(lead)
                save_leads(leads)
                print("Lead Delete Sucessfully....")
                found = True
                break
        if not found:
            print("Lead not  found")

    elif choice == '5':
        update_name = input("Enter the name to  Edit : ")
        for lead in leads:
            new_number = input("Enter the new Number : ")
            lead['number'] = new_number
            save_leads(leads)
            found = True
            break
        if not  found:
            print("Lead not  found")
    

    elif choice == '6' :
        print("Exit")
        break
    else :
        print("You  Are Selcted Wrong  Option. Please select  an Valid option")
