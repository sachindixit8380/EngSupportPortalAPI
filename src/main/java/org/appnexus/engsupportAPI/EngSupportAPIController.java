package org.appnexus.engsupportAPI;

import static org.springframework.hateoas.mvc.ControllerLinkBuilder.linkTo;
import static org.springframework.hateoas.mvc.ControllerLinkBuilder.methodOn;

import java.net.Authenticator;
import java.net.PasswordAuthentication;
import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
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
    	response.add(linkTo(methodOn(EngSupportAPIController.class).greeting(name)).withSelfRel());
        return new ResponseEntity<JSONText>(response, HttpStatus.OK);
    }
    
    
    @RequestMapping(value="/getAllAlerts")
    public HttpEntity<JSONText> getAllAlerts() {
    	return restOprImpl.getAllAlerts();
    }
    
    /**
     * @param alertStatus = Open, Acked, Closed etc; Default value = Open
     * @param alertCount = No of alerts to display, Eg: 10; Default value = 5
     * @param sortOrder = 0:Desc (Default), 1:Asc
     * @return
     */
    @RequestMapping(value={"/getAlerts","/getAlerts/{alertStatus}/{alertCount}/{sortOrder}","/getAlerts/{alertStatus}/{alertCount}", "/getAlerts/{alertStatus}" })
    public HttpEntity<JSONText> getAlerts(@PathVariable Optional<String> alertStatus, @PathVariable Optional<Integer> alertCount, @PathVariable Optional<Integer> sortOrder) {
    	return restOprImpl.getAlerts(alertStatus, alertCount, sortOrder);
    }
    
    @RequestMapping(value={"/getDownTimedAlerts"})
    public HttpEntity<JSONText> getDownTimedAlerts() {
    	return restOprImpl.getDownTimedAlerts();
    }

}