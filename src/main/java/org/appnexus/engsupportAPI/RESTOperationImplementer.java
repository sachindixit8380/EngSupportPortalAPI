package org.appnexus.engsupportAPI;

import static org.springframework.hateoas.mvc.ControllerLinkBuilder.linkTo;
import static org.springframework.hateoas.mvc.ControllerLinkBuilder.methodOn;

import java.io.IOException;
import java.text.ParseException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import org.appnexus.engsupportRESTClient.RESTClientService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.env.Environment;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.ifountain.opsgenie.client.OpsGenieClient;
import com.ifountain.opsgenie.client.OpsGenieClientException;
import com.ifountain.opsgenie.client.model.alert.ListAlertsRequest;
import com.ifountain.opsgenie.client.model.alert.ListAlertsResponse;
import com.ifountain.opsgenie.client.model.alert.AlertsRequest.Status;
import com.ifountain.opsgenie.client.model.beans.Alert;

@Component
public class RESTOperationImplementer {
	
    @Autowired
    private RESTClientService restClient;
    @Autowired
    private Environment env;

	JsonObject topAlerts = new JsonObject();

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
    	response.add(linkTo(methodOn(EngSupportAPIController.class).getDownTimedAlerts()).withSelfRel());

        return new ResponseEntity<JSONText>(response, HttpStatus.OK);
	}
	
	HttpEntity<JSONText> getTopAlerts() {
            getOpenAlerts();
            getClosedAlerts();
    		JSONText response = new JSONText(topAlerts.toString());
        	response.add(linkTo(methodOn(EngSupportAPIController.class).getDownTimedAlerts()).withSelfRel());

            return new ResponseEntity<JSONText>(response, HttpStatus.OK);
	}

	private void getOpenAlerts() {
    	String opsGenieApiKey = env.getProperty("opsgenie.appnexus.API.key");

    	OpsGenieClient client = new OpsGenieClient();

    	ListAlertsRequest request = new ListAlertsRequest();
    	request.setApiKey(opsGenieApiKey);
    	request.setLimit(5);
    	request.withStatus(Status.open);
    	List<String> listTags = new ArrayList<String>();
    	listTags.add("ANES");
    	request.setTags(listTags);
    	ListAlertsResponse response = null;
		try {
			response = client.alert().listAlerts(request);
		} catch (OpsGenieClientException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		} catch (ParseException e) {
			e.printStackTrace();
		}
    	List<Alert> alerts = response.getAlerts();

    	
    	JsonArray jsonArray = new JsonArray();

    	for(Alert alert: alerts) {

    		JsonObject jsonObject = new JsonObject();
    		jsonObject.addProperty("owner", alert.getOwner());
    		jsonObject.addProperty("message", alert.getMessage());

    		JsonArray jsonArrayTags = new JsonArray();
    		for(String tag:alert.getTags()) {
    			jsonArrayTags.add(tag);
    		}
    		jsonObject.add("tags", jsonArrayTags);

    		jsonObject.addProperty("alias", alert.getAlias());
    		jsonObject.addProperty("description", alert.getDescription());
    		jsonObject.addProperty("createdAt", alert.getCreatedAt());
    		jsonObject.addProperty("updatedAt", alert.getUpdatedAt());
    		jsonObject.addProperty("id", alert.getId());
    		jsonObject.addProperty("tinyId", alert.getTinyId());

    		JsonArray jsonArrayTeams = new JsonArray();
    		for(String team:alert.getTeams()) {
    			jsonArrayTeams.add(team);
    		}
    		jsonObject.add("teams", jsonArrayTeams);
    		jsonArray.add(jsonObject);
    	}

    	topAlerts.add("open_alerts", jsonArray);
	}

	private void getClosedAlerts() {
    	String opsGenieApiKey = env.getProperty("opsgenie.appnexus.API.key");

    	OpsGenieClient client = new OpsGenieClient();

    	ListAlertsRequest request = new ListAlertsRequest();
    	request.setApiKey(opsGenieApiKey);
    	request.setLimit(5);
    	request.withStatus(Status.closed);
    	List<String> listTags = new ArrayList<String>();
    	listTags.add("ANES");
    	request.setTags(listTags);
    	ListAlertsResponse response = null;
		try {
			response = client.alert().listAlerts(request);
		} catch (OpsGenieClientException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		} catch (ParseException e) {
			e.printStackTrace();
		}
    	List<Alert> alerts = response.getAlerts();

    	JsonArray jsonArray = new JsonArray();

    	for(Alert alert: alerts) {

    		JsonObject jsonObject = new JsonObject();
    		jsonObject.addProperty("owner", alert.getOwner());
    		jsonObject.addProperty("message", alert.getMessage());

    		JsonArray jsonArrayTags = new JsonArray();
    		for(String tag:alert.getTags()) {
    			jsonArrayTags.add(tag);
    		}
    		jsonObject.add("tags", jsonArrayTags);

    		jsonObject.addProperty("alias", alert.getAlias());
    		jsonObject.addProperty("description", alert.getDescription());
    		jsonObject.addProperty("createdAt", alert.getCreatedAt());
    		jsonObject.addProperty("updatedAt", alert.getUpdatedAt());
    		jsonObject.addProperty("id", alert.getId());
    		jsonObject.addProperty("tinyId", alert.getTinyId());

    		JsonArray jsonArrayTeams = new JsonArray();
    		for(String team:alert.getTeams()) {
    			jsonArrayTeams.add(team);
    		}
    		jsonObject.add("teams", jsonArrayTeams);
    		jsonArray.add(jsonObject);
    	}

    	topAlerts.add("closed_alerts", jsonArray);
	}
}
