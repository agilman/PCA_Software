from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from django.contrib.auth.models import User

from myApp.models import UserOrganizationRoleRel, Organization
from myApp.serializers import *
import datetime
import pytz

@csrf_exempt
def userRoles(request,userId=None):
    if request.method=='GET':
        #get current active roles.
        roles = UserOrganizationRoleRel.objects.filter(user = userId).filter(status=1).order_by('organization')
        roleResults = []

        for role in roles.all():
            org = role.organization
            #check if organiztion is already in results list
            if len(roleResults):
                if roleResults[len(roleResults)-1]["organization"]["id"] == org.id:
                    #append new roles to listed org
                    roleResults[len(roleResults)-1]["roles"].append(role.role)
                    roleResults[len(roleResults)-1]["roles"].sort()
                    
                else:
                    #add new organization
                    roleResults.append({'organization':{'id':org.id,'name':org.name,'logo':org.logo},'roles':[role.role]})
                    
            else:
                roleResults.append({'organization':{'id':org.id,'name':org.name,'logo':org.logo},'roles':[role.role]})

        #Add pending requests:
        pending = UserOrganizationRoleRel.objects.filter(user = userId).filter(status=0).all()
        serialized = UserOrgRoleSerializer(pending,many=True)

        finalResult = {"roles":roleResults,"pending":serialized.data}

        return JsonResponse(finalResult, safe=False)

    if request.method=='POST':
        data = JSONParser().parse(request)

        user = User.objects.get(pk=int(data["userId"]))        
        org = Organization.objects.get(id = data["orgId"])
        role = data["role"]
        acceptedBy = User.objects.get(pk=int(data["acceptedBy"]))
        now = datetime.datetime.now(pytz.timezone('US/Pacific'))
        
        request = UserOrganizationRoleRel(user=user,organization=org,role=role,status=1,approvedOrRejectedBy=acceptedBy,approvedOrRejectDate=now)
        request.save()

        serialized = OrgUsersSerializer(request)
        return JsonResponse(serialized.data, safe=False)
    
@csrf_exempt
def orgUsers(request,orgId=None):
    if request.method=="GET":        
        org = Organization.objects.get(id = orgId)
        query  = UserOrganizationRoleRel.objects.filter(organization=org)

        active = query.filter(status=1).all()
        pending = query.filter(status=0).all()
        
        activeSerialized = OrgUsersSerializer(active,many=True)
        pendingSerialized = OrgUsersSerializer(pending,many=True)

        result = {'active':activeSerialized.data,'pending':pendingSerialized.data}
        return JsonResponse(result, safe=False)
    
    if request.method=='POST':
        """This creates 'user join request'..."""
        data = JSONParser().parse(request)
        user = User.objects.get(pk=int(data["userId"]))
        
        org = Organization.objects.get(id = data["orgId"])

        now  = datetime.datetime.now(pytz.timezone('US/Pacific'))
        #If advStatus = active, need to unset previous active.
        
        request = UserOrganizationRoleRel(user=user,organization=org,role=1,request_date=now,status=0)
        request.save()

        serialized = UserOrgRoleSerializer(request)
        
        return JsonResponse(serialized.data, safe=False)

    if request.method == "PUT":
        data = JSONParser().parse(request)
        reqId = data["id"]
        now  = datetime.datetime.now(pytz.timezone('US/Pacific'))

        reqObj = UserOrganizationRoleRel.objects.filter(id=data['id']).update(status=data['status'],approvedOrRejectedBy=data['approvedOrRejectedBy'])

        #can't I return the reqObj ?
        modifiedObj = UserOrganizationRoleRel.objects.get(id=data['id'])
        serialized = OrgUsersSerializer(modifiedObj)
            
        return JsonResponse(serialized.data, safe=False)
        
@csrf_exempt
def orgList(request):
    if request.method == "GET":
        """Returns list of all organizations, friendly for dropdown by region"""
        results = []
        for org in Organization.objects.all().order_by("location"):
            if len(results)==0: #if there are no items in list, add new item

                results.append({"location":org.location,"orgs":[OrgSerializer(org).data]})
            else: #if there are items in the list..

                if results[len(results)-1]["location"]==org.location: #if location already exists in results... append new org to that location
                    results[len(results)-1]["orgs"].append(OrgSerializer(org).data)
                else:
                    results.append({"location":org.location,"orgs":[OrgSerializer(org).data]})

        return JsonResponse(results, safe=False)

@csrf_exempt
def orgWorkers(request,orgId=None):
    if request.method == "GET":
        """Returns list of all active workers in an organizations"""
        org = Organization.objects.get(id=orgId)
        query = UserOrganizationRoleRel.objects.filter(status=1).filter(role=1).filter(organization=org)

        result = query.all()
        serialized = OrgUsersSerializer(result,many=True)
        

        return JsonResponse(serialized.data, safe=False)

@csrf_exempt
def donation(request,orgId=None):
    if request.method == "POST":
        #POST INPUT:
        #{donor:{},donation:{}}
        #Where donor can be an ID of an existing donor, or a new donor.
        #output: donation. Possibly donor also saved, and check and credit card.
        
        data = JSONParser().parse(request)
        donor = data["donor"]
        donation = data["donation"]
        user = User.objects.get(pk=donation["user"]) #this refers to 'worker' or recruiter...
        org = Organization.objects.get(id=donation["org"])
        
        donorObj = None
        now = datetime.datetime.now(pytz.timezone('US/Pacific'))
        addedBy = User.objects.get(pk=request.user.id)
        #if got donor description
        if hasattr(donor,'id'):
            donorObj = Donor.objects.get(id=donor['id'])
    
        else:
            name = donor["name"]
            addr = donor["addr"]
            city = donor["city"]
            state= donor["state"]
            zipcode = donor["zip"]
            email = donor["email"]
            phone = donor["phone"]
            over18 = bool(int(donor["over18"]))
            
            donorObj = Donor(user=user,org=org,name=name,addr=addr,city=city,state=state,zipcode=zipcode,email=email,phone=phone,over18=over18,addedOn=now,addedBy=addedBy)
            donorObj.save()
        
        donationType = int(donation["donationType"])
        dateLi = donation["date"].split()
        date = datetime.date(int(dateLi[0]),int(dateLi[1]),int(dateLi[2]))
        donationObj = None
        value = donation["value"]

        donationObj = Donation(user=user,org=org, formDate=date, donor = donorObj, donationType=donationType, value=value, addedOn = now,addedBy=addedBy)
        donationObj.save()
        if donationType==1: #cash donation
            pass
            
        elif donationType==2:
            #Also save CC
            nameOnCard = donation["nameOnCard"]
            cardLast4 = donation["cardLast4"]
            cardExp = donation["cardExp"]
            cardRecurring = donation['cardRecurring']
            
            ccObj = CreditCard(donation=donationObj,nameOnCard=nameOnCard,last4=cardLast4,exp = cardExp,recurring=cardRecurring)
            ccObj.save()
            
        elif donationType==3:
            #also save check
            checkNum = donation["checkNum"]
            dateLi = donation["checkDate"].split()
            checkDate = datetime.date(int(dateLi[0]),int(dateLi[1]),int(dateLi[2]))
            
            checkObj = Check(donation=donationObj,checkNum=checkNum,checkDate=checkDate,status=0)
            checkObj.save()
            
        serialized = DonationSerializer(donationObj)
        return JsonResponse(serialized.data, safe=False)

@csrf_exempt
def donationHist(request,userId=None,orgId=None):
    if request.method == "GET":
        """Returns list of all active workers in an organizations"""
        user = User.objects.get(pk=userId)
        org = Organization.objects.filter(id=orgId)


        query = Donation.objects.filter(user=user).filter(org=org).order_by("-formDate") #Todo... filter last 30 days.
        results = query.all()

        serialized = DonationSerializer(results,many=True)
        
        return JsonResponse(serialized.data, safe=False)

    
@csrf_exempt
def hours(request,userId=None,orgId=None):
    if request.method == "GET":
        user = User.objects.get(pk=userId)
        org = Organization.objects.get(id=orgId)

        hoursQuery = Hours.objects.filter(user=user).filter(org=org)
        results = hoursQuery.all()

        serialized = HoursSerializer(results,many=True)
        return JsonResponse(serialized.data,safe=False)
                                
        
    if request.method == "POST":
        data = JSONParser().parse(request)

        user = User.objects.get(pk=data["userId"])
        org = Organization.objects.get(id=data["orgId"])
        
        date = data["date"]
        htype = data["type"]
        hours = data["hours"]
        addedBy = User.objects.get(pk=data["addedBy"])
        now = datetime.datetime.now(pytz.timezone('US/Pacific'))
            
        newHours = Hours(user=user,org=org,date=date,hoursType=htype,hours=hours,addedBy=addedBy,addedOn=now)
        newHours.save()

        serialized = HoursSerializer(newHours)
        
        return JsonResponse(serialized.data, safe=False)
        
"""
@csrf_exempt
def form1(request,userId=None,orgId=None):
    if request.method == "GET":
        user = User.objects.get(pk=userId)
        allForm1s = Form1.objects.filter(user=user)

        history = allForm1s.filter(status=1).all()

        histResult = []
        for i in history:
            rDict = Form1Serializer(i).data
            total = i.totalDonations()
            rDict["total"] = total
            histResult.append(rDict)
        
        return JsonResponse({'history':histResult},safe=False)

    if request.method == "POST":
        data = JSONParser().parse(request)
        formJson = data["form1"]
        userId = formJson["userId"]
        user = User.objects.get(pk=userId)
        orgId = formJson["orgId"]
        org = Organization.objects.get(id=orgId)
        dateStr = formJson["date"]
        date = datetime.strptime(dateStr,"%m-%d-%Y").date()
        canvassHours = formJson["canvassHours"]
        #otherHours = data["otherHours"]
        trf=formJson["trf"]
            
        newForm = Form1(user=user,org=org,date=date,canvassHours=canvassHours,otherHours=0,trf=trf,status=1)
        newForm.save()

        donationsJson = data["donations"]
        total = 0
        for donation in donationsJson:
            chk = donation['chk']
            cc = donation['cc']
            money = donation['money']

            newDonation = Donation(form=newForm,chk=chk,cc=cc,money=money)
            newDonation.save()

            total+= float(money)

        fDict = Form1Serializer(newForm).data
        fDict["total"] = total
        
        return JsonResponse(fDict,safe=False)
    
    
    """  """
    if request.method == "PUT":
        data = JSONParser().parse(request)
        if len(data.keys()) == 2:
            formId = data['id']
            status = data['status']

            f = Form1.objects.get(id=formId)
            f.status = status
            f.save()

            serialized = Form1Serializer(f).data
            total = f.totalDonations()
            serialized["total"] = total
            
        return JsonResponse(serialized, safe=False)
    """ """ 
        
@csrf_exempt
def donation(request):
    pass
    """ """
    if request.method == "POST":
        data = JSONParser().parse(request)
        formJson = data["form"]
        chk = data['chk']
        cc = data['cc']
        money = data['money']

        formId = formJson;
        if type(formJson)==type({}): #if got dictionary instead of formId (need to create form1)
            userId = formJson["userId"]
            user = User.objects.get(pk=userId)
            orgId = formJson["orgId"]
            org = Organization.objects.get(id=orgId)
            dateStr = formJson["date"]
            date = datetime.strptime(dateStr,"%m-%d-%Y").date()
            canvassHours = formJson["canvassHours"]
            #otherHours = data["otherHours"]
            trf=formJson["trf"]
            
            newForm = Form1(user=user,org=org,date=date,canvassHours=canvassHours,otherHours=0,trf=trf,status=0)
            newForm.save()

            formId = newForm.id

        form = Form1.objects.get(id=formId)
        newDonation = Donation(form=form,chk=chk,cc=cc,money=money)
        newDonation.save()

        serialized = DonationSerializer(newDonation)
        
        
        return JsonResponse(serialized.data, safe=False)
    """
