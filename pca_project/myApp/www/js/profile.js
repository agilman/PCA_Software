
var myApp = angular.module('userApp', ['ui.router','ui.bootstrap']);

myApp.config(function($stateProvider){
    $stateProvider
        .state('profile', {
	    url: "/",
	    templateUrl: '/www/partials/profile.html',
	    controller: 'ProfileController'
	})
        .state('bookkeeper',{
	    url:"/org/:orgId/bookkeeper",
	    templateUrl: '/www/partials/bookkeeper.html',
	    controller: 'BookkeeperController'
	})
        .state('bookkeeper.userMgmt',{
	    url:"/userMgmt",
	    templateUrl: '/www/partials/bookkeeper-userMgmt.html',
	    controller: 'BkprUsrMgmtController'
	})
        .state('bookkeeper.payterms',{
	    url:"/payterms",
	    templateUrl: '/www/partials/bookkeeper-payterms.html',
	    controller: 'BkprPaytermsController'
	})
        .state('manager',{
	    url:"/org/:orgId/manager",
	    templateUrl: '/www/partials/manager.html',
	    controller: 'ManagerController'
	})
        .state('manager.donors',{
	    url:"/donors",
	    templateUrl: '/www/partials/manager-donors.html',
	    controller: 'ManagerDonorsController'
	})
        .state('manager.hours',{
	    url:"/hours",
	    templateUrl: '/www/partials/manager-hours.html',
	    controller: 'ManagerHoursController'
	})
        .state('manager.form1',{
	    url:"/form1",
	    templateUrl: '/www/partials/forms/form1.html',
	    controller: 'Form1Controller'
	})
        .state('manager.form2',{
	    url:"/form2",
	    templateUrl: '/www/partials/forms/form2.html',
	    controller: 'Form2Controller'
	})
        .state('worker',{
	    url:"/org/:orgId/worker",
	    templateUrl: '/www/partials/worker.html',
	    controller: 'WorkerController'
	});
});

myApp.controller('mainController', ['$scope','$http','$log','$stateParams', function($scope,$http,$log,$stateParams) {
    $scope.userId = document.getElementById('userId').value;
    $scope.userName = document.getElementById('userName').value;
    $scope.orgList = [];

    //TODO FIX THIS ... OrgList is used to populate org list dropdown in /profile ,
    //  Also this information used to get org name in org page...
    $http.get('/api/rest/orgList').then(function(data){
	$scope.orgList = data.data;
    });    
}]);

myApp.controller('ProfileController', ['$scope','$http','$log', function($scope,$http,$log) {
    $scope.profilePic = '/www/img/blank-profile-picture-973460_960_720.png';

    $scope.userOrgs = [];
    $scope.userPendingOrgs = [];
    
    $http.get('/api/rest/userRoles/' + $scope.userId).then(function(data){
	$scope.userOrgs = data.data.roles;
	$scope.userPendingOrgs = data.data.pending;
    });
    
    $scope.getRoleName=function(roleNum){
	if (roleNum==1){
	    return "Worker"
	}else if (roleNum==2){
	    return "Manager"
	}else if (roleNum==3){
	    return "Bookkeeper"
	}
    };

    function checkIfMember(orgId){
	for (var i = 0;i<$scope.userOrgs.length;i++){
	    if ($scope.userOrgs[i].organization.id == orgId){
		return true;
	    }
	}
	return false;
    }

    function checkIfMembershipPending(orgId){
	for (var i=0; i<$scope.userPendingOrgs.length;i++){
	    if($scope.userPendingOrgs[i].organization==orgId){
		return true;
	    }
	}
	
	return false;
    }
    
    $scope.joinClick = function(){
	var newOrgId = document.getElementById("orgList").value;

	if (checkIfMember(newOrgId)){
	    alert("Already a member");
	}else if(checkIfMembershipPending(newOrgId)){
	    alert("A request to join already exists");
	}else{
	    var newRequest = {'userId':$scope.userId,'orgId':newOrgId};
	    $http.post('/api/rest/orgUsers/'+newOrgId ,JSON.stringify(newRequest)).then(function(data){
		$scope.userPendingOrgs.push(data.data);
	    });
	}
    };

    $scope.getOrgName = function(orgId){
	for (var i = 0; i < $scope.orgList.length; i++){
	    var locationOrgs = $scope.orgList[i].orgs;
	    
	    for (var p = 0; p < locationOrgs.length; p++){
		var org = locationOrgs[p];
		if(org.id == orgId){
		    return org.name;
		}
	    }
	}
    }
}]);

myApp.controller('BookkeeperController', ['$scope','$http','$log','$stateParams', function($scope,$http,$log,$stateParams) {
    $scope.orgId = $stateParams.orgId;
    $scope.orgName= null;

    //Set org name
    for(var i=0;i<$scope.orgList.length;i++){
	var locationList = $scope.orgList[i].orgs;
	for(var p=0;p<locationList.length;p++){
	    if (locationList[p].id==$scope.orgId){
		$scope.orgName=locationList[p].name;
	    }
	}
    }
    
    $scope.selectedForm = null;
    $scope.isFormActive = function(formIndex){	
	if ( $scope.selectedForm == formIndex){
	    return "active";
	}
    };
    
    $scope.$on("selectForm",function(event,formIndex){
	$scope.selectedForm = formIndex;
    });

    $log.log("hello from Bookkeeper controller");

}]);

myApp.controller('BkprUsrMgmtController', ['$scope','$http','$log','$stateParams', function($scope,$http,$log,$stateParams) {
    $scope.$emit("selectForm",1);
    $log.log("Hello from Bookkeeper User Mgmt controller");

    $scope.bookkeepers = [];
    $scope.managers = [];
    $scope.workers = [];
    $scope.pending = [];
    
    //Areas: Bookkeepers, managers, workers, pending requests
    $scope.pendingRequests = [];
    $http.get('/api/rest/orgUsers/' + $scope.orgId).then(function(data){
	for(var i=0;i<data.data.active.length ;i++){
	    var usrRole = data.data.active[i].role;
	    if (usrRole==1){
		$scope.workers.push(data.data.active[i]);
	    } else if (usrRole==2){
		$scope.managers.push(data.data.active[i]);
	    } else if (usrRole==3){
		$scope.bookkeepers.push(data.data.active[i]);
	    }
	}

	$scope.pending = data.data.pending;	
    });

    $scope.acceptUserRequest = function(indx){
	var request = $scope.pending[indx];	
	var reqUpdated = {'id':request.id,'user':request.userInfo.pk,'organization':request.organization,'status':1,'approvedOrRejectedBy':$scope.userId};
	
	$http.put('/api/rest/orgUsers/'+$scope.orgId ,JSON.stringify(reqUpdated)).then(function(data){
	    //Remove from Pending, add to Workers.
	    $scope.pending.splice(indx,1);
	    
	    $scope.workers.push(data.data);
	});	
    }
    
    $scope.rejectUserRequest = function(indx){
	$log.log("REJECT!");
    }

    $scope.isBookkeeper = function(userId){
	for(var i=0; i<$scope.bookkeepers.length; i++){
	    if ($scope.bookkeepers[i].userInfo.pk==userId){
		return true;
	    }
	}
	return false;
    }
    
    $scope.isManager = function(userId){
	for(var i=0; i<$scope.managers.length; i++){
	    if ($scope.managers[i].userInfo.pk==userId){
		return true;
	    }
	}
	return false;
    }

    $scope.addBookkeeperPermissions = function(index){
	var usr = $scope.workers[index];
	var data = {'userId':usr.userInfo.pk,
		    'orgId':$scope.orgId,
		    'role':3,
		    'acceptedBy':$scope.userId,
		   };
	
	$http.post('/api/rest/userRoles/'+usr.userInfo.pk,JSON.stringify(data)).then(function(data){
	    $scope.bookkeepers.push(data.data);
	});
    }
    
    $scope.addManagerPermissions = function(index){
	var usr = $scope.workers[index];
	var data = {'userId':usr.userInfo.pk,
		    'orgId':$scope.orgId,
		    'role':2,
		    'acceptedBy':$scope.userId,
		   };
	
	$http.post('/api/rest/userRoles/'+usr.userInfo.pk,JSON.stringify(data)).then(function(data){
	    $scope.managers.push(data.data);
	});
	
    }
}]);

myApp.controller('BkprPaytermsController', ['$scope','$http','$log','$stateParams', function($scope,$http,$log,$stateParams) {
    $scope.$emit("selectForm",2);
    $scope.userTerms = [];
    $scope.editing = null;
    $scope.tempBaseRate = null;
    $scope.baseRateChanged=false;
    $scope.newTempRate = null;
    $scope.newcomerShare = null
    $scope.newcomerShareChanged = false;
    
    $scope.today = function() {
	$scope.dt = new Date();
	$scope.dt2 = new Date();
	$scope.dt2.setDate($scope.dt.getDate() + 7);

    };
    $scope.today();
    $scope.popup1 = {
	opened: false
    };

    $scope.popup2 = {
	opened: false
    };
    $scope.open1 = function() {
	$scope.popup1.opened = true;
    };

    $scope.open2 = function() {
	$scope.popup2.opened = true;
    };

    $scope.startChanged = function(){
	$scope.dt2 = new Date()
	$scope.dt2.setDate($scope.dt.getDate()+7);
    };
    
    function getDateIndex(userId){
	for(var i=0;i<$scope.userTerms.length;i++){
	    if($scope.userTerms[i].userInfo.pk==userId){
		return i;
	    }
	}
	
	return -1;
    };

    function addToBase(term,usrIndex){
	//This function replaces base terms as needed.
	if ($scope.userTerms[usrIndex].terms.base.length==0){
	    $scope.userTerms[usrIndex].terms.base.push(term);
	}else{
	    if (term.id > $scope.userTerms[usrIndex].terms.base[0].id){ //replace if new item has higher id...
		$scope.userTerms[usrIndex].terms.base=[term];
	    }
	}
	
    }

    function addToTemp(term,usrIndex){
	//This function replaces temp terms as needed.
	if ($scope.userTerms[usrIndex].terms.temp.length==0){
	    $scope.userTerms[usrIndex].terms.temp.push(term);
	}else{
	    if (term.id > $scope.userTerms[usrIndex].terms.temp[0].id){ //replace if new item has higher id...
		$scope.userTerms[usrIndex].terms.temp=[term];
	    }
	}
    }

    function addTerms(termsLi){
	//Adds a list of user terms to $schope.userTerms
	for (var i=0;i<termsLi.length;i++){
	    var term = termsLi[i]
	    var usrIndex = getDateIndex(term.userInfo.pk);
	    if (usrIndex==-1){ //if user terms doesn't exist, create them.
		
		if (term.termsType==1){
		    $scope.userTerms.push({'userInfo':term.userInfo,'terms':{'base':[term],'temp':[]}  }  );
		}else if (term.termsType==2){
		    $scope.userTerms.push({'userInfo':term.userInfo,'terms':{'base':[],'temp':[term]} });
		}
	    }else{ //if user terms exist,		
		//only store latest of each type.

		if (term.termsType==1){
		    addToBase(term,usrIndex);
		}else if (term.termsType==2){
		    addToTemp(term,usrIndex);
		}
	    }
	}
    }
    
    $http.get('/api/rest/payTerms/' + $scope.orgId).then(function(data){
	$scope.userTerms=[];
	addTerms(data.data);
    });


    $http.get('/api/rest/newcomerShare/' + $scope.orgId).then(function(data){
	$scope.newcomerShare = data.data.newcomerShare;
	
    });

    $scope.editUserTerms = function(userIndx){
	$scope.editing = $scope.userTerms[userIndx];
	$scope.tempBaseRate = $scope.editing.terms.base[0].percent;

	if ($scope.editing.terms.temp.length){ //if temporary terms are active, load start and end date, and rate.
	    $scope.newTempRate = $scope.editing.terms.temp[0].percent;

	    var sdate  =  $scope.editing.terms.temp[0].startDate.split('-');
	    var edate  =  $scope.editing.terms.temp[0].endDate.split('-');
	    $scope.dt  = new Date(sdate);
	    $scope.dt2 = new Date(edate);

	}
    };

    $scope.saveNewBaseTerms = function(){
	$log.log("save base rate");

	var data = {'user':$scope.editing.userInfo.pk,
		    'org': $scope.orgId,
		    'termsType': 1,
		    'percent': $scope.tempBaseRate,
		    'addedBy': $scope.userId,
		   };
	
	$http.post('/api/rest/payTerms/'+$scope.orgId,JSON.stringify(data)).then(function(data){
	    $log.log(data.data);
	    addTerms([data.data]);
	    $log.log("OK");
	});
	
	//hide button
	$scope.baseRateChanged=false;
    };
    
    $scope.saveNewTempTerms = function(){
	$log.log("save temp terms");

	var data = {'user':$scope.editing.userInfo.pk,
		    'org': $scope.orgId,
		    'termsType': 2,
		    'percent': $scope.newTempRate,
		    'startDate' : moment($scope.dt).format('YYYY-MM-DD'),
		    'endDate': moment($scope.dt2).format('YYYY-MM-DD'),
		    'addedBy': $scope.userId,
		   };
	
	$http.post('/api/rest/payTerms/'+$scope.orgId,JSON.stringify(data)).then(function(data){
	    addTerms([data.data]);
	});
	//hide button
	$scope.tempRateChanged=false;
    };

    $scope.saveNewcomerShare = function(){
	var data = {'org': $scope.orgId,
		    'settingName': 'newcomerShare',
		    'settingValue': $scope.newcomerShare,
		    'addedBy': $scope.userId,
		   };
	
	$http.post('/api/rest/newcomerShare/'+$scope.orgId,JSON.stringify(data)).then(function(data){
	    //addTerms([data.data]);
	    $scope.newcomerShareChanged = false;
	    $scope.editNewcomerShare=false;
	});

    };

    
    
    $log.log("Hello from Bookkeeper Payterms  controller");
}]);


myApp.controller('ManagerController', ['$scope','$http','$log','$stateParams', function($scope,$http,$log,$stateParams) {
    $scope.orgId = $stateParams.orgId;
    $scope.orgName= null;
    $scope.selectedForm = null;
    $scope.isFormActive = function(formIndex){	
	if ( $scope.selectedForm == formIndex){
	    return "active";
	}
    };
  
    $scope.$on("selectForm",function(event,formIndex){
	$scope.selectedForm = formIndex;
    });

    //Set org name
    for(var i=0;i<$scope.orgList.length;i++){
	var locationList = $scope.orgList[i].orgs;
	for(var p=0;p<locationList.length;p++){
	    if (locationList[p].id==$scope.orgId){
		$scope.orgName=locationList[p].name;
	    }
	}
    }    
}]);


myApp.controller('ManagerDonorsController', ['$scope','$http','$log','$stateParams', function($scope,$http,$log,$stateParams) {
    $scope.$emit("selectForm",1);
    $scope.dt = new Date();
    $scope.checkDt = new Date();
    $scope.donorName=null;
    $scope.donorAddr=null;
    $scope.donorCity=null;
    $scope.donorState=null;
    $scope.donorZip=null;
    $scope.donorEmail=null;
    $scope.donorPhone=null;
    $scope.donationType=1;
    $scope.nameOnCard=null;
    $scope.cardLast4=null;
    $scope.cardExp=null;
    $scope.cardRecurring=0;
    $scope.checkNum=null;
    $scope.selectedWorker = null;
    $scope.donorOver18 = "1";
    $scope.donationValue = 0 ;
    
    //history section
    $scope.history = [];

    $scope.oneAtAtime=true; //thid doesn't work?
    //init status for each item in history...
    $scope.histStatus = {'isOpen':[]};
    $scope.initHist = function(){
	
	for (var i =0;i< $scope.history.length;i++){
	    $scope.histStatus[i]=false;
	};
	if ($scope.history.length){
	    $scope.histStatus.isOpen[0]=true;
	}
    };
        
    //datepicker things
    $scope.today = function() {
	$scope.dt = new Date();
	$scope.checkDt = new Date();
    };
    $scope.today();
    $scope.popup1 = {
	opened: false
    };

    $scope.popup2 = {
	opened: false
    };
    $scope.open1 = function() {
	$scope.popup1.opened = true;
    };

    $scope.open2 = function() {
	$scope.popup2.opened = true;
    };

    //Get org workers list.
    $scope.workers = [];
    $http.get('/api/rest/orgWorkers/' + $scope.orgId).then(function(data){
	$scope.workers = data.data;
    });    

    $scope.submitClick = function(){
	var donor = { 'user': $scope.selectedWorker.userInfo.pk,
		      'org': $scope.orgId,
		      'name': $scope.donorName,
		      'addr': $scope.donorAddr,
		      'city': $scope.donorCity,
		      'state': $scope.donorState,
		      'zip': $scope.donorZip,
		      'email': $scope.donorEmail,
		      'phone': $scope.donorPhone,
		      'over18': $scope.donorOver18};

	var donation = null;
	if ($scope.donationType==1){ //cash donation
	    donation = {'user': $scope.selectedWorker.userInfo.pk,
			'org': $scope.orgId,
			'donationType' : $scope.donationType,
			'date': moment($scope.dt).format("YYYY MM DD"),
			'value': $scope.donationValue
		       };
	}else if ($scope.donationType==2){ //Credit Card
	    donation = {'user': $scope.selectedWorker.userInfo.pk,
			'org': $scope.orgId,
			'donationType' : $scope.donationType,
			'date': moment($scope.dt).format("YYYY MM DD"),
			'value': $scope.donationValue,
			//Credid Card specific
			'nameOnCard': $scope.nameOnCard,
			'cardLast4' : $scope.cardLast4,
			'cardExp'   : $scope.cardExp,
			'cardRecurring': $scope.cardRecurring,
		       };
	    $log.log(donation);
	    
	}else if ($scope.donationType==3){ //check
	    donation = {'user': $scope.selectedWorker.userInfo.pk,
			'org': $scope.orgId,
			'donationType' : $scope.donationType,
			'date': moment($scope.dt).format("YYYY MM DD"),
			'value': $scope.donationValue,
			//Check specific
			'checkNum':$scope.checkNum,
			'checkDate':moment($scope.checDt).format("YYYY MM DD"),
		       };
	}

	var data = {'donor':donor,'donation':donation};
	$http.post('/api/rest/donation',JSON.stringify(data)).then(function(data){
	    //Add new entry to history.
	    addDonations([data.data]);
	    	    
	    //clear form
	    $scope.donorName=null;
	    $scope.donorAddr=null;
	    $scope.donorCity=null;
	    $scope.donorState=null;
	    $scope.donorZip=null;
	    $scope.donorEmail=null;
	    $scope.donorPhone=null;
	    $scope.donorOver18 = "1";	    
	    $scope.donationValue = 0 ;
	    //cc specific
	    $scope.nameOnCard=null;
	    $scope.cardLast4=null;
	    $scope.cardExp=null;
	    $scope.cardRecurring=0;  
	    //check specific
	    $scope.checkNum=null;
	    $scope.checkDt = new Date(); //Maybe refresh formDate as well?
	});
    };

    function getDateIndex(date){
	for(var i=0;i<$scope.history.length;i++){
	    if($scope.history[i].formDate==date){
		return i;
	    }
	}

	return -1;
    };

    function addDonations(donLi){
	//Adds a list of donations to $schope.history
	for (var i=0;i<donLi.length;i++){
	    var donation = donLi[i]
	    var dateIndex = getDateIndex(donation.formDate);
	    if (dateIndex==-1){ //if date doesn't exist in hist, create it.
		$scope.history.push({'formDate':donation.formDate,'donations':[donation]});
	    }else{ //if date exists, need to append to donations for that day.
		$scope.history[dateIndex].donations.push(donation);
	    }   
	}
    }
    
    $scope.recruiterChange = function(userId){
	//get user donation history for past 30 days
	$http.get('/api/rest/donationHist/' + userId+'/'+$scope.orgId).then(function(data){
	    $scope.history=[];
	    var donations = data.data;
	    addDonations(donations);//Add donations to history format...
	});	
    };

    $scope.donationTypeStr = function(type){
	if (type=='1'){
	    return "Cash";
	}else if (type=='2'){
	    return "Credit Card";
	}else if (type=='3'){
	    return "Check";
	}
    };

    $scope.dayTotal = function(dayIndx){
	var day = $scope.history[dayIndx];
	var sum = 0;
	for(var i = 0;i<day.donations.length;i++){
	    sum += day.donations[i].value;
	}
	return sum;
    };
    
}]);

myApp.controller('ManagerHoursController', ['$scope','$http','$log','$stateParams', function($scope,$http,$log,$stateParams) {
    $scope.$emit("selectForm",2);

    $scope.dt = new Date();
    $scope.workers = [];
    $scope.selectedWorker=null;
    $scope.hoursType="1";
    $scope.hours=4;
    $scope.history = [];
    //init status for each item in history...
    $scope.histStatus = {'isOpen':[]};
    $scope.initHist = function(){
	
	for (var i =0;i< $scope.history.length;i++){
	    $scope.histStatus[i]=false;
	};
	if ($scope.history.length){
	    $scope.histStatus.isOpen[0]=true;
	}
    };
    
    //date stuff
    $scope.today = function() {
	$scope.dt = new Date();
    };
    $scope.today();
    $scope.popup1 = {
	opened: false
    };

    $scope.open1 = function() {
	$scope.popup1.opened = true;
    };

    //Get org workers list.
    $http.get('/api/rest/orgWorkers/' + $scope.orgId).then(function(data){
	$scope.workers = data.data;
    });
    
    $scope.addHours = function(){
	var date = moment($scope.dt).format('YYYY-MM-DD');
	var hours = {'userId':$scope.selectedWorker.userInfo.pk,'date':date,'type': $scope.hoursType, 'orgId':$scope.orgId,'hours':$scope.hours,'addedBy':$scope.userId};
	
	$http.post("/api/rest/hours/"+$scope.selectedWorker.userInfo.pk+"/"+$scope.orgId,JSON.stringify(hours)).then(function(data){
	    addHours([data.data]);

	    //need to process data.data
	});
    }

    function getDateIndex(date){
	for(var i=0;i<$scope.history.length;i++){
	    if($scope.history[i].date==date){
		return i;
	    }
	}

	return -1;
    };

    //NAMING IS CONFUSING
    //$scope.addHours adds hours by POST request
    //This addHours process data and adss it to $scope.history
    function addHours(hoursLi){
	//Adds a list of donations to $schope.history
	for (var i=0;i<hoursLi.length;i++){
	    var day = hoursLi[i]
	    var dateIndex = getDateIndex(day.date);
	    if (dateIndex==-1){ //if date doesn't exist in hist, create it.
		$scope.history.push({'date':day.date,'hours':[day]});
	    }else{ //if date exists, need to append to donations for that day.
		$scope.history[dateIndex].hours.push(day);
	    }   
	}
    }
    
    $scope.workerChange = function(userId){
	//get user donation history for past 30 days
	$http.get('/api/rest/hours/' + userId+'/'+$scope.orgId).then(function(data){
	    $scope.history=[];
	    addHours(data.data);//Add hours to history format...
	});	
    };

    $scope.dayTotal = function(index){
	var day = $scope.history[index];
	var sum = 0;
	for(var i = 0;i<day.hours.length;i++){
	    sum += day.hours[i].hours;
	}
	return sum;
	
    };
    
    $scope.hoursTypeStr = function(type){
	if (type=='1'){
	    return "Canvassing";
	}else if (type=='2'){
	    return "Admin";
	}else if (type=='3'){
	    return "Travel";
	}
    };
    
}]);

myApp.controller('Form1Controller', ['$scope','$http','$log','$stateParams', function($scope,$http,$log,$stateParams) {
    $scope.$emit("selectForm",3);
    
    $scope.canvassHours=4;
    $scope.trf="";
    $scope.donations = [];
    $scope.chk = "";
    $scope.cc = "";
    $scope.money = 0.0;
    $scope.form1 = null;
    $scope.submitHistory=[];

    //validators
    $scope.isMoneyNumber = function(){
	var mon = !isNaN($scope.money);
	return mon;
    }
    
    //datepicker things
    $scope.today = function() {
	$scope.dt = new Date();
    };
    $scope.today();
    $scope.popup1 = {
	opened: false
    };
    $scope.open1 = function() {
	$scope.popup1.opened = true;
    };
    
    //get only history. No unfinished forms are stored.
    $http.get('/api/rest/form1/' + $scope.userId+'/'+$scope.orgId).then(function(data){
	$scope.submitHistory = data.data.history;
    });
    
    $scope.addDonation = function(){
	//No need for this... form1 gets created on 'submitClick'
	//if form1 is null, need to create it first
	/*
	var form1 = $scope.form1;
	if (form1==null){
	    var date = moment($scope.dt).format('MM-DD-YYYY');
	    
	    form1 = {'userId':$scope.userId,'date':date,'orgId':$scope.orgId,'canvassHours':$scope.canvassHours,'trf':$scope.trf};
	}else{
	    form1 = $scope.form1.id;
	}
	*/
	var donation = {'chk': $scope.chk,'cc':$scope.cc,'money':$scope.money};
	$scope.donations.push(donation);
	
	//TODO REMOVE THIS API CALL
	/*$http.post('/api/rest/donation',JSON.stringify(donation)).then(function(data){
	    //need to set $scope.form1
	    if($scope.form1==null){
		$scope.form1 = form1;
		$scope.form1.id=data.data.form;		
	    }
	});
	*/
	
	//clear values
	$scope.chk = "";
	$scope.cc ="";
	$scope.money = "";
    };
    
    $scope.submitClick=function(){
	var date = moment($scope.dt).format('MM-DD-YYYY');
	var form1 = {'userId':$scope.userId,'date':date,'orgId':$scope.orgId,'canvassHours':$scope.canvassHours,'trf':$scope.trf};
	var form1Data = {"form1":form1,"donations":$scope.donations}
	//var formId = $scope.form1.id;
	//var update = {'id':formId,'status':1};

	//TODO REMOVE PUT FROM API...
	/*
	$http.put('/api/rest/form1/'+$scope.userId,JSON.stringify()).then(function(data){
	    $scope.submitHistory.push(data.data);
	});
	*/

	$http.post('/api/rest/form1/'+$scope.userId,JSON.stringify(form1Data)).then(function(data){
	    $scope.submitHistory.push(data.data);

	    $scope.donations=[];
	});
    };
}]);

myApp.controller('Form2Controller', ['$scope','$http','$log','$stateParams', function($scope,$http,$log,$stateParams) {
    $scope.$emit("selectForm",4);
}]);


myApp.controller('WorkerController', ['$scope','$http','$log','$stateParams', function($scope,$http,$log,$stateParams) {
    $log.log("Hello from Worker Controller");
}]);
