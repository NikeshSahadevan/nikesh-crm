from storage import load_leads
from  crm  import add_lead, search_lead, delete_lead, update_lead

leads = load_leads()

while True:
    choice = input("\n1. Add Lead\n2. View Leads\n3. Search Lead\n4. Delete Lead\n5. Update Lead\n6. Exit\nEnter choice: ")

    if choice == '1':
        name = input("Enter the Name: ")
        number = input("Enter the Mobile Number: ")
        add_lead(leads, name, number)
        print("Lead added successfully!")

    elif choice == '2':
        if not leads:
            print("No Leads Available")
        else:
            for lead in leads:
                print(f"Name : {lead['name']}, Phone : {lead['number']}")

    elif choice == '3':
        search_name = input("Enter name to search: ")
        results = search_lead(leads, search_name)
        if results:
            for lead in results:
                print(f"Found : {lead['name']} - Phone : {lead['number']}")
        else:
            print("No lead found with that name.")

    elif choice == '4':
        delete_name = input("Enter name to Delete: ")
        if delete_lead(leads, delete_name):
            print("Lead deleted successfully!")
        else:
            print("Lead not found.")

    elif choice == '5':
        old_name = input("Enter the name of the  lead to update : ")
        new_name = input("ُEnter new name (press Enter to keep current : )")
        new_number = input("Enter the mobile number (press Enter to keep  current : )")
        if update_lead(leads,old_name,new_name,new_number) :
            print("Lead Updated Sucessfully!")
        else :
            print("Lead not  Found.")

    elif choice == '6':
        print("Exit")
        break

    else:
        print("You have selected an invalid option. Please select a valid option.")