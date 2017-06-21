package org.appnexus.engsupportAPI;

import java.text.SimpleDateFormat;
import java.util.Date;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.quartz.Job;
import org.quartz.JobExecutionContext;
import org.quartz.TriggerKey;
import org.quartz.impl.triggers.SimpleTriggerImpl;
import org.springframework.stereotype.Component;


@Component
public class NotifyEndofDowntime implements Job{
	@Override
	public void execute(JobExecutionContext jobContext)  {
		String id = (String) jobContext.getJobDetail().getJobDataMap().get("id");
		String until = (String) jobContext.getJobDetail().getJobDataMap().get("until");
		String  response = ( (RESTOperationImplementer) jobContext.getJobDetail().getJobDataMap().get("callerInstance")).getAllDownTimedAlerts();
		String downtimed_alerts = response; 
   	  
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
				   System.out.println(existing_until+" "+until + " "+existing_until.equals(until));
				   if(existing_until.equals(until))
				   {
					  // Call Python url , pass user_name and Job id
				   }
				   else
				   {
				   //update scheduler
				   SimpleTriggerImpl simpleTrigger = new SimpleTriggerImpl();
				   SimpleDateFormat  formatter = new SimpleDateFormat("yyyy-M-dd HH:mm:ss");
				   Date d1 = formatter.parse(existing_until);
				   long timeMilli = d1.getTime();
				   simpleTrigger.setStartTime(new Date(timeMilli - 600000));
                   RESTOperationImplementer.scheduler.rescheduleJob(TriggerKey.triggerKey(id),simpleTrigger);
				   return;
				   }	   
			}
			else{
	    	   //do nothing
			} 
		 }
		 } 
		 catch (Exception e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
		}
	}
}