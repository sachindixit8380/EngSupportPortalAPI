package org.appnexus.engsupportAPI;

import java.net.Authenticator;
import java.net.PasswordAuthentication;
import java.util.Optional;

import javax.ws.rs.PathParam;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class EngSupportAPIController {

    private static final String TEMPLATE = "Hello, %s!";
    
    @Autowired
    private RESTOperationImplementer restOprImpl;

//    @Autowired
//    private TokenAuthenticationService tokenService;

    public EngSupportAPIController() {
    	//temporary code to provide authentication to call REST calls
    	//DigestAuthenticator dd = new DigestAuthenticator().authenticate(request, httpResponse)
    	Authenticator.setDefault(new Authenticator() {
     	    @Override
     	    protected PasswordAuthentication getPasswordAuthentication() {          
     	        return new PasswordAuthentication("sdixit", "Aveeno@8083".toCharArray());
     	    }
     	});
    }
    
    @RequestMapping(value="/greeting")
    public @ResponseBody HttpEntity<JSONText> greeting(
            @RequestParam(value = "name", required = false, defaultValue = "World") String name) {

    	JSONText response = new JSONText(String.format(TEMPLATE, name));
    	//response.add(linkTo(methodOn(EngSupportAPIController.class).greeting(name)).withSelfRel());
        return new ResponseEntity<JSONText>(response, HttpStatus.OK);
    }
    
    
    @RequestMapping(value={"/getTopOpsGenieAlerts","/getTopOpsGenieAlerts/{alertCount}"})
    public HttpEntity<String> getAllAlerts( @PathVariable(required=false) Integer alertCount) {
    	if(alertCount == null)
    		alertCount = 5;
    	return restOprImpl.getTopOpsGenieAlerts(alertCount);
    }
    
    /**
     * @param alertStatus = Open, Acked, Closed etc; Default value = Open
     * @param alertCount = No of alerts to display, Eg: 10; Default value = 5
     * @param sortOrder = 0:Desc (Default), 1:Asc
     * @return
     */
    @RequestMapping(value={"/getAllEarlyBirdAlerts"})
    public HttpEntity<String> getAllEarlyBirdAlerts() {
    	return restOprImpl.getAllEarlyBirdAlerts();
    }
    
    @RequestMapping(value={"/getAllDownTimedAlerts"})
    public HttpEntity<String> getAllDownTimedAlerts() {
    	return restOprImpl.getAllDownTimedAlertsAndScheduleDT();
    }
    
    @RequestMapping(value={"/downTimeOrClearAlert/{action}/{serviceName}/{alertDS}/{alertHost}/{alertDT}/{alertUser}"})
    public HttpEntity<String> downTimeOrClearAlert(@PathVariable String action, @PathVariable String serviceName, @PathVariable String alertDS, @PathVariable String alertHost, @PathVariable String alertDT, @PathVariable String alertUser) {
    	return restOprImpl.downTimeOrClearAlert(action, serviceName, alertDS, alertHost, alertDT, alertUser);
    }

}