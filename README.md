# Neighbor Hackathon

AI Prompt:
You are going to create UI and scaffold for a single-page application to help with the job search. The application will use python with the django framework. The UI should contain a search bar where users can search for networking events by career focus and location. The page should be dynamic and update the list of events based on the search query, with filters for date, time, and distance. Each event should be displayed in a card format displaying the title, date, time, location, and a description. The card should take you to the source URL on click. Do not display a field if not given. 

The data should be sourced from dummy data. The data should take the form of a list of model objects. Here is the definition of the model class:
class event:
    sourceURL: string
    title: string
    start_time: datetime
    end_time: string
    location
    description: string

Use a design that will be extensible and open for adding new features easily.