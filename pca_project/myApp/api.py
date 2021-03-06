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
        """This is where requests are rejected or accepted... status gets updated"""
        data = JSONParser().parse(request)
        reqId = data["id"]
        now  = datetime.datetime.now(pytz.timezone('US/Pacific'))

        reqObj = UserOrganizationRoleRel.objects.filter(id=data['id']).update(status=data['status'],approvedOrRejectedBy=data['approvedOrRejectedBy'])

        #can't I return the reqObj ?
        modifiedObj = UserOrganizationRoleRel.objects.get(id=data['id'])
        serialized = OrgUsersSerializer(modifiedObj)

        #If this is new user joining an organization, payterms are created.
        if modifiedObj.role==1 and data['status']==1:
            user = modifiedObj.user
            org = modifiedObj.organization

            #get percent for newcomers...
            #TODO GET THIS NUMBER FROM pca_project/settings.py
            newcomerShare = 50
            orgSetting = OrgSettings.objects.filter(org=org).filter(settingName="newcomerShare").all()
            if len(orgSetting):
                newcomerShare=float(orgSetting[0].settingValue)                

            newTerms = PayTerms(user=user,org=org,termsType=1,percent=newcomerShare)
            newTerms.save()

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

def getPayTerms(user,org):
    payTerms = user.payterms_set.filter(org=org)

    #check if user has temporary pay terms
    tempTerms = payTerms.filter(startDate__lte=datetime.date.today()).filter(endDate__gt=datetime.date.today()).all()
    if len(tempTerms):  #use latest temp terms...
        return tempTerms[len(tempTerms)-1]     

    
    else:
        baseRate = payTerms.filter(termsType=1).all()
        if len(baseRate):

            return baseRate[len(baseRate)-1]

        else:
            return None

    
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
        user = User.objects.get(pk=donation["user"]) #this refers to 'worker' or 'recruiter'...
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

        #Get curently applied payTerms
        payTerms = getPayTerms(user,org)
        

        donationObj = Donation(user=user,org=org, payTerms = payTerms, formDate=date, donor = donorObj, donationType=donationType, value=value, addedOn = now,addedBy=addedBy)
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
            
            checkObj = Check(donation=donationObj,checkNum=checkNum,checkDate=checkDate)
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
    
@csrf_exempt
def payTerms(request, orgId=None):
    if request.method == "GET":
        #Get all Users and their payterms for the org.
        #filter here? or in UI?
        terms = PayTerms.objects.filter(org=orgId)

        serialized = PayTermsSerializer(terms,many=True)
        return JsonResponse(serialized.data, safe=False)

    if request.method == "POST":
        data = JSONParser().parse(request)
        
        user = User.objects.get(pk=int(data["user"]))
        org = Organization.objects.get(id = data["org"])
        termsType = data["termsType"]
        percent = data["percent"]
        addedBy = User.objects.get(pk=int(data["addedBy"]))
        now = datetime.datetime.now(pytz.timezone('US/Pacific'))

        pt = None 
        if termsType==1: #base terms
            pt = PayTerms(user=user, org=org, termsType=termsType, percent=percent ,addedBy=addedBy, addedOn=now)
        elif termsType==2:
            startDate = data['startDate']
            endDate = data['endDate']
            
            pt = PayTerms(user=user, org=org, termsType=termsType, percent=percent ,startDate=startDate,endDate=endDate, addedBy=addedBy, addedOn=now)
            
        pt.save()

        serialized = PayTermsSerializer(pt)
        return JsonResponse(serialized.data, safe=False)


@csrf_exempt
def payRates(request, orgId=None):
    if request.method == "GET":
        org = Organization.objects.get(id=orgId)
        rates = PayRate.objects.filter(org=org)

        serialized = PayRatesSerializer(rates, many=True)

        return JsonResponse(serialized.data, safe = False)

    if request.method == "POST":
        org = Organization.objects.get(id=orgId)
        
        data = JSONParser().parse(request)

        hoursType = data["hoursType"]
        rate = data["rate"]
        startDate = data["startDate"]

        setBy = User.objects.get(pk=request.user.id)
        now = datetime.datetime.now(pytz.timezone('US/Pacific'))
        
        newRate = PayRate(org=org, hoursType=hoursType, rate = rate, startDate = startDate, setBy = setBy, setOn = now)
        newRate.save()

        serialized = PayRatesSerializer(newRate)
        
        return JsonResponse(serialized.data, safe = False)
        
@csrf_exempt
def newcomerShare(request,orgId=None):
    if request.method == "GET":
        org = Organization.objects.get(id=orgId)
        setting = OrgSettings.objects.filter(org=org).filter(settingName="newcomerShare")
        result = 0;

        if setting.count()==0:
            #TODO GET THIS VALUE FROM settings.py
            result = 50
        else:        
            result = setting.last().settingValue

        return JsonResponse({'newcomerShare':result}, safe=False)

    if request.method == "POST":
        data = JSONParser().parse(request)

        org = Organization.objects.get(id=data["org"])
        settingValue = data["settingValue"]
        
        addedBy = User.objects.get(pk=int(data["addedBy"]))
        now = datetime.datetime.now(pytz.timezone('US/Pacific'))
        
        newVal = OrgSettings(org=org,settingName="newcomerShare",settingValue=settingValue,addedBy=addedBy,addedDate=now)
        newVal.save()
        
        return JsonResponse({'newcomerShare':settingValue}, safe=False)


@csrf_exempt
def adjustments(request,orgId=None,year=None):
    if request.method =="GET":
        org = Organization.objects.get(id=orgId)
        donations = Donation.objects.filter(org=org).filter(donationType__in=[2,3]).filter(formDate__year=year).all()

        serialized = AdjustmentsReportSerializer(donations,many=True)

        return JsonResponse(serialized.data ,safe=False)

    elif request.method =="POST":
        data = JSONParser().parse(request)

        donation = Donation.objects.get(id=data["donationId"])
        status = data["status"]
        fee = data["fee"]
        notes = ""
        
        addedBy = User.objects.get(pk=request.user.id)
        now = datetime.datetime.now(pytz.timezone('US/Pacific'))
        
        newAdjustment = DonationAdjustment(donation=donation,status=status,fee=fee,notes=notes, proccessedBy=addedBy, proccessedOn=now)
        newAdjustment.save()

        serialized = AdjustmentsReportSerializer(donation)
        return JsonResponse(serialized.data, safe=False)


@csrf_exempt
def reimbursementRequests(request,orgId=None,year=None,canvId=None):
    if request.method == "GET":
        org = Organization.objects.get(id=orgId)
        
        query = ReimbursementRequest.objects.filter(org=org).filter(date__year=year)
           
        if int(canvId)!=0:
            canv = User.objects.get(pk=int(canvId))
            query = query.filter(workerId=canv)

        objs = query.all()
        serialized = ReimbursementRequestSerializer(objs,many=True)
            
        return JsonResponse(serialized.data,safe=False)
        
    if request.method == "POST":
        data = JSONParser().parse(request)

        org = Organization.objects.get(id=orgId)
        worker = User.objects.get(pk=canvId)

        date = data["date"]
        payee = data["payee"]
        reimType = data["type"]
        purpose = data["purpose"]
        amount = str(float(data["amount"]))

        requestedBy = User.objects.get(pk=request.user.id)
        now = datetime.datetime.now(pytz.timezone('US/Pacific'))

        newRequest = ReimbursementRequest(org=org,workerId=worker,date=date,payee=payee,reimType=reimType,purpose=purpose,amount=amount,requestedBy=requestedBy, requestedOn = now)
        newRequest.save()
        
        serialized = ReimbursementRequestSerializer(newRequest)

        return JsonResponse(serialized.data,safe=False)


@csrf_exempt
def reimbursementResponses(request,requestId=None):
    if request.method=="POST":
        raw= JSONParser().parse(request)
        data = raw["request"]
        reimbRequest = ReimbursementRequest.objects.get(id=requestId)

        status = data["status"]
        reviewedBy = User.objects.get(pk=data["reviewer"]["userInfo"]["pk"])
        
        dateLi = raw["simpleDate"].split('-')
        reviewedOn = datetime.date(int(dateLi[0]),int(dateLi[1]),int(dateLi[2]))

        responder = User.objects.get(pk=request.user.id)
        now = datetime.datetime.now(pytz.timezone('US/Pacific'))

        newResponse = ReimbursementResponse(request=reimbRequest,status=status,reviewedBy=reviewedBy,reviewedOn=reviewedOn,respondedBy=responder,respondedOn=now)
        newResponse.save()

        serialized = ReimbursementRequestSerializer(reimbRequest)
        
        return JsonResponse(serialized.data,safe=False)

def getNextInvoiceNum(org):
    lastInvoice = Invoice.objects.filter(org=org).last()
    
    if lastInvoice==None:
        return 1
    
    else:
        return lastInvoice.invNum+1

@csrf_exempt
def nextInvoiceNum(request,orgId=None):
    org = Organization.objects.get(id=orgId)     
    nextNum = getNextInvoiceNum(org)
    
    return JsonResponse({'nextNum':nextNum},safe=False)

@csrf_exempt
def invoices(request,orgId=None):
    if request.method=="GET":
        org = Organization.objects.get(id=orgId)
        invoices = Invoice.objects.filter(org=org).all()

        serialized = InvoiceSerializer(invoices,many=True)
        return JsonResponse(serialized.data,safe=False)
        
    if request.method=="POST":
        data = JSONParser().parse(request)
        
        org = Organization.objects.get(id = orgId)
        invNum = getNextInvoiceNum(org)
        billFrom = data["from"]
        billTo = data["billTo"]
        addr = data["addr"]
        state = data["state"]
        zip = data["zip"]
        date = data["date"]
        
        newInvoice = Invoice(org=org, invNum=invNum, billFrom=billFrom, billTo=billTo,addr=addr,state=state,zip=zip, date=date)
        newInvoice.save()

        #save invoice items
        for item in data["items"]:
            description = item["description"]
            amount = item["amount"]
            tax = 0
            newItem = InvoiceItem(invoice=newInvoice,description=description,amount=amount,tax=tax)
            newItem.save()

        serialized = InvoiceSerializer(newInvoice)
        return JsonResponse(serialized.data, safe=False)

@csrf_exempt
def workerManagement(request,relId=None,orgId=None):
    if request.method == "GET":
        """Returns unassigned workers as well as managers with assigned workers"""
        #unassigned workers
        
        #all workers....
        workers = UserOrganizationRoleRel.objects.filter(organization=orgId).filter(role=1).filter(status=1)
        assignedWorkersLi = ManagerWorkerRel.objects.filter(endDate=None).filter(org=orgId).values_list('worker',flat=True)
        
        #Need to remove from workers the ones that have a manager
        unassignedWorkers = workers.exclude(user__in=assignedWorkersLi)
        
        #get data about workers from user table
        unassignedWorkersData = User.objects.filter(pk__in=unassignedWorkers.values_list('user',flat=True))
        unassignedSerialized = UserSerializer(unassignedWorkersData.all(),many=True)

    
        #get active managers
        activeManagers = UserOrganizationRoleRel.objects.filter(organization = orgId).filter(role=2).filter(status=1)
        managers = User.objects.filter(pk__in=activeManagers.values_list('user',flat=True))
        
        #serilize maangers, and get list of their workers through managerWorkerRel_set
        managersSerialized = ManagerWorkerSerializer(managers,many=True)
        
        return JsonResponse({'unassigned':unassignedSerialized.data,
                         'managers':managersSerialized.data},safe=False)

    if request.method == "POST":
        data = JSONParser().parse(request)
        
        manager = User.objects.get(pk=int(data["manager"]))
        org = Organization.objects.get(id = data["org"])
        worker =  User.objects.get(pk=int(data["worker"]))
        startDate = data['startDate']

        assignedBy = User.objects.get(pk=request.user.id)
        assignedOn = datetime.datetime.now(pytz.timezone('US/Pacific'))

        assignment = ManagerWorkerRel(manager=manager,org=org,worker=worker,startDate=startDate,endDate=None,assignedBy=assignedBy,assignedOn=assignedOn)
        assignment.save()

        serialized = WorkerSerializer(assignment)
        
        return JsonResponse(serialized.data, safe=False)

    if request.method == "PUT":
        data = JSONParser().parse(request)
        
        rel = ManagerWorkerRel.objects.get(id=relId)
        rel.endDate = data["endDate"]
        rel.save()

        worker = User.objects.get(pk=data["workerId"])
        serialized = UserSerializer(worker)
        
        return JsonResponse(serialized.data,safe=False)
    
#Reports
@csrf_exempt
def orgYTDDonations(request,orgId=None,year=None):
    if request.method == "GET":
        #Get donations for given year. Recurring CC donations are proccessed differently from cash and check donations.
        #Donation types: cash=1 , CC=2, check=3
        
        org = Organization.objects.get(id=orgId)
        donations1 = Donation.objects.filter(org=org).filter(formDate__year=year).all()
    
        serialized = Donations1Serializer(donations1,many=True)
        return JsonResponse(serialized.data, safe=False)

@csrf_exempt
def c2wReport(request,orgId=None,start=None,end=None):
    if request.method=="GET":
        org = Organization.objects.get(id=orgId)
        
        myStart = start.split("-")
        mySDate = datetime.date(int(myStart[0]),int(myStart[1]),int(myStart[2]))
        
        myEnd = end.split("-")
        myEDate = datetime.date(int(myEnd[0]),int(myEnd[1]),int(myEnd[2]))
        
        #TODO, check that start and end dates are reasonable...
        donations1 = Donation.objects.filter(org=org).filter(formDate__gte=mySDate).filter(formDate__lt=myEDate).all()
        
        #Get hours
        hours = Hours.objects.filter(org=org).filter(date__gte=mySDate).filter(date__lt = myEDate).all()
        
        serializedDonations = Donations1Serializer(donations1,many=True)
        serializedHours = HoursSerializer(hours,many=True)
        
        return JsonResponse({"donations":serializedDonations.data,"hours":serializedHours.data}, safe=False)

