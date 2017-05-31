package org.appnexus.engsupportAPI;

import static org.springframework.hateoas.mvc.ControllerLinkBuilder.linkTo;
import static org.springframework.hateoas.mvc.ControllerLinkBuilder.methodOn;

import java.util.Optional;

import org.appnexus.engsupportRESTClient.RESTClientService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.env.Environment;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;

@Component
public class RESTOperationImplementer {
	
    @Autowired
    private RESTClientService restClient;
    @Autowired
    private Environment env;
    
	HttpEntity<JSONText> getAllAlerts() 
	{
		JSONText response = new JSONText(restClient.callRestService(env.getProperty("niteowl.API.baseURL") + "/alerts/alert"));
    	response.add(linkTo(methodOn(EngSupportAPIController.class).getAllAlerts()).withSelfRel());

        return new ResponseEntity<JSONText>(response, HttpStatus.OK);
	}

/**
 * @param alertStatus = Open, Acked, Closed etc; Default value = Open
 * @param alertCount = No of alerts to display, Eg: 10; Default value = 5
 * @param sortOrder = 0:Desc (Default), 1:Asc
 * @return
 */
HttpEntity<JSONText> getAlerts(@Value("Open") Optional<String> alertStatus, @Value("5") Optional<Integer> alertCount, @Value("0") Optional<Integer> sortOrder) 
	{
		JSONText response = new JSONText(restClient.callRestService(env.getProperty("niteowl.API.baseURL") + "/alerts/alert"));
    	response.add(linkTo(methodOn(EngSupportAPIController.class).getAllAlerts()).withSelfRel());

        return new ResponseEntity<JSONText>(response, HttpStatus.OK);
	}

/**
 * @return
 */
	HttpEntity<JSONText> getDownTimedAlerts() 
	{
		JSONText response = new JSONText(restClient.callRestService(env.getProperty("niteowl.API.baseURL") + "/alerts/filter"));
    	response.add(linkTo(methodOn(EngSupportAPIController.class).getAllAlerts()).withSelfRel());

        return new ResponseEntity<JSONText>(response, HttpStatus.OK);
	}
}
