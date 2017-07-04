package org.appnexus.engsupportAPI;

import java.io.IOException;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.ResultSet;
import java.sql.Statement;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Optional;
import java.util.TimeZone;
import org.appnexus.engsupportRESTClient.RESTClientService;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.quartz.JobBuilder;
import org.quartz.JobDetail;
import org.quartz.Scheduler;
import org.quartz.SchedulerFactory;
import org.quartz.impl.StdSchedulerFactory;
import org.quartz.impl.triggers.SimpleTriggerImpl;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.env.Environment;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.RequestParam;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.ifountain.opsgenie.client.OpsGenieClient;
import com.ifountain.opsgenie.client.OpsGenieClientException;
import com.ifountain.opsgenie.client.model.alert.AlertsRequest.Status;
import com.ifountain.opsgenie.client.model.alert.ListAlertsRequest;
import com.ifountain.opsgenie.client.model.alert.ListAlertsResponse;
import com.ifountain.opsgenie.client.model.beans.Alert;

@Component
public class RESTOperationImplementer {
	
    @Autowired
    private RESTClientService restClient;
    @Autowired
    private Environment env;

    private String dbURL="jdbc:mysql://107.sdixit.user.nym2.adnexus.net";

    private String dbUser="sdixit";

    private String dbPass="july1980";

    private Connection conn = null;
	JsonObject completeObject = new JsonObject();

	JSONParser parser = new JSONParser();
    SchedulerFactory factory = new StdSchedulerFactory();
    static Scheduler scheduler = null;
    
    RESTOperationImplementer()
    {
    }

    private int insertOrClearDownTimedAlerts(String action, String serviceName, String alertDS, String alertHost, String alertDT, String alertUser)
    {
		   PreparedStatement stmt = null;
		   String sql = null;
		   stmt = null;
		   int k=0;
		   if(conn==null)
		   {
			   try{
				      Class.forName("com.mysql.jdbc.Driver");
				      //System.out.println("Connecting to database...");
				      conn = DriverManager.getConnection( dbURL + "?user=" + dbUser + "&password=" + dbPass);
				      conn.setAutoCommit(true);
				  }
			   catch(Exception e) 
			   {
				   e.printStackTrace();
			   }
		   }
		   try {
			   if(action.equals("downtime"))
		       {
				   sql = "replace into engsupportportal.DownTimedAlerts values (?, ?, ?, ?, ?)"; 
				   stmt = conn.prepareStatement(sql);
				   stmt.setString(1, serviceName + ":" + alertDS + ":" + alertHost);
				   stmt.setString(2,serviceName);
				   stmt.setString(3, alertDS);
				   stmt.setString(4, alertDT);
				   stmt.setString(5, alertUser);
		       }
			   if(action.equals("clear"))
			   {
				   sql = "delete from engsupportportal.DownTimedAlerts where id=?"; 
				   stmt = conn.prepareStatement(sql);
				   stmt.setString(1, serviceName + ":" + alertDS + ":" + alertHost);
			   }
		       k = stmt.executeUpdate();
		   } catch (SQLException e) {
			// TODO Auto-generated catch block
			   e.printStackTrace();
		   }
		   return k;
    }
    
    HttpEntity<String> getAllEarlyBirdAlerts() 
	{
		JSONText response = new JSONText(restClient.callRestService(env.getProperty("niteowl.API.baseURL") + "/alerts/alert"));
    	//response.add(linkTo(methodOn(EngSupportAPIController.class).getAllAlerts()).withSelfRel());

        return new ResponseEntity<String>(response.getContent().toString(), HttpStatus.OK);
	}


	 String getAllDownTimedAlerts() 
	{
		JSONText response = new JSONText(restClient.callRestService(env.getProperty("niteowl.API.baseURL") + "/alerts/filter"));
    	//response.add(linkTo(methodOn(EngSupportAPIController.class).getAllAlerts()).withSelfRel());

        return response.getContent().toString();
	}
	
	HttpEntity<String> getTopOpsGenieAlerts(int alertCount) {//Refreshes the list of alerts
		completeObject.entrySet().clear();
		getOpenClosedAlerts(alertCount);
        JSONText response = new JSONText(completeObject.toString());
        return new ResponseEntity<String>(response.getContent().toString(), HttpStatus.OK);
	}

	private void getOpenClosedAlerts(int alertCount) {
    	String opsGenieApiKey = env.getProperty("opsgenie.appnexus.API.key");

    	OpsGenieClient client = new OpsGenieClient();

    	ListAlertsRequest request = new ListAlertsRequest();
    	request.setApiKey(opsGenieApiKey);
    	request.setLimit(alertCount);
    	request.withStatus(Status.open);
    	List<String> listTags = new ArrayList<String>();
    	listTags.add("ANES");
    	request.setTags(listTags);
    	ListAlertsResponse response = null;
		try {
			response = client.alert().listAlerts(request);
		} catch (OpsGenieClientException | IOException | ParseException e) {
			e.printStackTrace();
		} 
    	List<Alert> alertsOpen = response.getAlerts();

    	//getClosed Alerts
    	request.withStatus(Status.closed);
		try {
			response = client.alert().listAlerts(request);
		} catch (OpsGenieClientException | IOException | ParseException e) {
			e.printStackTrace();
		} 
    	List<Alert> alertsClosed = response.getAlerts();

    	List<Alert> alerts = alertsOpen;
		JsonArray jsonArray = new JsonArray();
    	
		for(int i=0;i<2;i++)
    	{	
			jsonArray = new JsonArray();
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
	    	if(!completeObject.has("open_alerts"))
	    		completeObject.add("open_alerts", jsonArray.getAsJsonArray());
	    	alerts = alertsClosed;
    	}
    		if(!completeObject.has("closed_alerts"))
    			completeObject.add("closed_alerts", jsonArray.getAsJsonArray());
	}


	 HttpEntity<String> getAllDownTimedAlertsAndScheduleDT()  
	    {
		 TimeZone.setDefault(TimeZone.getTimeZone("UTC"));
		 String response = getAllDownTimedAlerts();
		 
		   try {
			   scheduler = factory.getScheduler();
			   scheduler.clear();
			   scheduler.start();
	  
	    	   String downtimed_alerts = response.toString(); 
	    	  
	           Object obj = parser.parse(downtimed_alerts);
	           JSONObject jsonObject = (JSONObject) obj;
			   JSONArray response_array = (JSONArray) jsonObject.get("response");
		   
		       for (int i = 0; i < response_array.size(); i++) {
				   JSONObject row = (JSONObject) response_array.get(i);
				   String id = String.valueOf(row.get("id"));
				   String until = (String) (row.get("until"));
				   String user =  (String) (row.get("user")); 
				   
				   JobDetail job = JobBuilder.newJob(NotifyEndofDowntime.class).withIdentity(id,"downtimeAlerts").build();
				   job.getJobDataMap().put("id",id);
				   job.getJobDataMap().put("user",user);
				   job.getJobDataMap().put("until",until);
				   job.getJobDataMap().put("callerInstance",this);
				 
				   SimpleDateFormat  formatter = new SimpleDateFormat("yyyy-M-dd HH:mm:ss");
				   formatter.setTimeZone(TimeZone.getTimeZone("UTC"));
				   Date d1 = formatter.parse(until);
				   long timeMilli = d1.getTime();
				  
				   SimpleTriggerImpl simpleTrigger = new SimpleTriggerImpl();
				   simpleTrigger.setName(id);
				   simpleTrigger.setGroup("downtimeAlerts");
				 
				   //Schedule all downtime for (downtime - 10 mins)
				   simpleTrigger.setStartTime(new Date(timeMilli - 600000));
				   scheduler.scheduleJob(job, simpleTrigger);
			}
			   if (conn == null) {
				conn = getDBConnection();
			}

			         Statement stmt = conn.createStatement();
			         ResultSet rs = stmt.executeQuery("select * from engsupportportal.DowntimedAlerts");
			   
			  while (rs.next()) {

				String id = rs.getString("id");
				String until = rs.getString("alert_downtime");
				String user = rs.getString("alert_user");

				JobDetail job = JobBuilder.newJob(NotifyEndofDowntime.class).withIdentity(id,"downtimeAlerts").build();

				job.getJobDataMap().put("id", id);
				job.getJobDataMap().put("user", user);
				job.getJobDataMap().put("until", until);
				job.getJobDataMap().put("callerInstance", this);

				long timeMilli = Long.parseLong(until);
				timeMilli = (timeMilli * 1000L) - 600000;
				SimpleDateFormat formatter = new SimpleDateFormat("yyyy-M-dd HH:mm:ss");
				formatter.setTimeZone(TimeZone.getTimeZone("UTC"));
				Date date = formatter.parse(String.valueOf(timeMilli));

				SimpleTriggerImpl simpleTrigger = new SimpleTriggerImpl();
				simpleTrigger.setName(id);
				simpleTrigger.setGroup("downtimeAlerts");
				simpleTrigger.setStartTime(date);

				scheduler.scheduleJob(job, simpleTrigger);

			}

			
		} catch (Exception e) {
			
			e.printStackTrace();
		}
		return new ResponseEntity<String>(response, HttpStatus.OK);
		
    }
	HttpEntity<String> downTimeOrClearAlert(String action, String serviceName, String alertDS, String alertHost, String alertDT, String alertUser) {
			if(action == null)
				return new ResponseEntity<String>("Error", HttpStatus.OK);
			else
				insertOrClearDownTimedAlerts(action, serviceName, alertDS, alertHost, alertDT, alertUser);
			
			//Refresh Scheduler list
			getAllDownTimedAlertsAndScheduleDT();
            return new ResponseEntity<String>("Success", HttpStatus.OK);
	}
}
