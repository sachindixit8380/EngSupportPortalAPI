package org.appnexus.engsupportRESTClient;


import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

@Service
public class RESTClientService {
	RestTemplate restClient; 
	
	public RESTClientService() {
		restClient = new RestTemplate();
	}
	public String callRestService(String restURL)
	{
		try
		{
			return restClient.getForObject(restURL, String.class);
		}
		catch (RestClientException re)
		{
			return "Exception while calling service " + restURL + ". " + re.getMessage();
		}
		catch (Exception e)
		{
			return "Fatal exception while calling service " + restURL + ". " + e.getMessage();
		}
	}
}
