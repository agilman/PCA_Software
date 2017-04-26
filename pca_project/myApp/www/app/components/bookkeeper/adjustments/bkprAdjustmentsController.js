myApp.controller('BkprAdjustmentsController', ['$scope','$http','$log','$stateParams', function($scope,$http,$log,$stateParams) {
    $scope.$emit("selectForm",3);

    $scope.canvId = $stateParams.canvId;
    $scope.canvassers = [];
    
    var y = moment().format("YYYY");
    $scope.yearOptions = [y,y-1,y-2,y-3];
    $scope.selectedYear = $stateParams.year;

    $scope.rawAdjData = null;
    $scope.unproccessedCCs = [];
    $scope.processedCCs = [];
    $scope.recurringCCs = [];
    $scope.unproccessedCKs = [];
    $scope.proccessedCKs = [];

    $scope.fee = parseFloat(1.0);
    
    function selectCanvsr(){
	for(var i=0; i<$scope.canvassers.length; i++){
	    if($scope.canvId==$scope.canvassers[i].userInfo.pk){
		$scope.selectedCnvsr=$scope.canvassers[i];
	    }
	}
    }

    //get canvassers list
    $http.get('/api/rest/orgWorkers/' + $scope.orgId).then(function(data){
	$scope.canvassers =[{'userInfo':
			     {'pk':0,
			      'first_name':"All",
			      'last_name':""}}];
	
	//push
	for (var i=0;i<data.data.length;i++){
	    $scope.canvassers.push(data.data[i]);
	}
	
	//select canvasser
	selectCanvsr();
    });

    function addUnproccessedCC(donation){
	var x = donation;
	x.adjustments.push({'status':null});
	$scope.unproccessedCCs.push(x);
    }

    function addUnproccessedCK(donation){
	var x = donation;
	x.adjustments.push({'status':null});
	$scope.unproccessedCKs.push(x);
    }

    function sortRawAdjs(){
	for(var i=0;i<$scope.rawAdjData.length;i++){
	    var donation = $scope.rawAdjData[i];
	    if (donation.donationType==2){
		//check recurring

		//else 
		if (donation.adjustments.length==0){
		    addUnproccessedCC(donation);
		    
		}else{
		    //$scope.proccessedCCs.push(donation);
		}
	    } else if (donation.donationType==3){
		if (donation.adjustments.length==0){
		    addUnproccessedCK(donation);
		}else{
		    //$scope.proccessedChecks.push(donation);
		}
	    }
	}
    }

    //get all credit card and check transactions for the year
    $http.get('/api/rest/orgAdjustments/' + $scope.orgId+"/"+ $scope.selectedYear).then(function(data){
	$scope.rawAdjData = data.data;
	
	sortRawAdjs();
    });

    $scope.saveCCAdjustment = function(index){
	var donation = $scope.unproccessedCCs[index];
	
	var data = {'donationId': donation.id,
		    'status': donation.adjustments.status,
		    'fee': $scope.fee};	

	$http.post('/api/rest/orgAdjustments/',JSON.stringify(data)).then(function(data){
	    //addAdjustments([data.data]);
	    $scope.unproccessedCCs.splice(index,1);
	});	
		
    }

    $scope.saveCKAdjustment = function(index){
	var donation = $scope.unproccessedCKs[index];

	var data = {'donationId': donation.id,
		    'status': donation.adjustments.status,
		    'fee': $scope.fee};
	

	
	$http.post('/api/rest/orgAdjustments/',JSON.stringify(data)).then(function(data){
	    $scope.unproccessedCKs.splice(index,1);
	});		
    }
    
    $log.log("Hello from Bookkeeper Adjustmentss  controller");
}]);