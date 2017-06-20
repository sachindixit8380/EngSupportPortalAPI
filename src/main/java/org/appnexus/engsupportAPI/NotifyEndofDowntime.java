package org.appnexus.engsupportAPI;

import org.quartz.Job;
import org.quartz.JobExecutionContext;
import org.springframework.stereotype.Component;

@Component
public class NotifyEndofDowntime implements Job {

	RESTOperationImplementer restImpl;

	@Override
	public void execute(JobExecutionContext jobContext)  {
	
			
		String id = (String) jobContext.getJobDetail().getJobDataMap().get("id");
		String until = (String) jobContext.getJobDetail().getJobDataMap().get("until");
		
		System.out.println("In Job execution >> "+until);
				
		// JSONText  response = new JSONText(restClient.callRestService(env.getProperty("niteowl.API.baseURL") + "/alerts/filter"));
	     //@SuppressWarnings("unused")
		//JSONText  response = ( (RESTOperationImplementer) jobContext.getJobDetail().getJobDataMap().get("callerInstance")) .getDownTimedAlerts();
		/*String downtimed_alerts = response.getContent(); 
   	  
		 try {
		 
		 JSONParser parser = new JSONParser();
         Object obj = parser.parse(downtimed_alerts);
		
         JSONObject jsonObject = (JSONObject) obj;
		 JSONArray response_array = (JSONArray) jsonObject.get("response");
	   
	 
	       for (int i = 0; i < response_array.size(); i++) {
	    	   
	    	   
	    	   JSONObject row = (JSONObject) response_array.get(i);
				 
	    	   String existing_id = String.valueOf(row.get("id"));
	    	   String existing_until = (String) (row.get("until"));
			   if(existing_id.equals(id))
					   {
				   
				    
				   if(existing_until.equals(until))
				   {
				   
					  // Call Python url , pass user_name and Job id
					   
					   System.out.println(" From here I will do CURL");
			
				   }
				   else
				   {
					   //update scheduler
					  
					   SimpleTriggerImpl simpleTrigger = new SimpleTriggerImpl();
					   
					   
					   SimpleDateFormat  formatter = new SimpleDateFormat("yyyy-M-dd HH:mm:ss");
					   formatter.setTimeZone(TimeZone.getTimeZone("UTC"));
					   Date d1 = formatter.parse(existing_until);
					   long timeMilli = d1.getTime();
					   
					   simpleTrigger.setStartTime(new Date(timeMilli - 600000));
					   
			           RESTOperationImplementer.scheduler.rescheduleJob(TriggerKey.triggerKey(id),simpleTrigger);
					   
					   return;
					   
					   
				   }	   
	       }else{
	    	   
	    	   //do nothing
	    	   return;
	       } 
	       }
		
		 } catch (Exception e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		*/
		 
		
		
	}

}