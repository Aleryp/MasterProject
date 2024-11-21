# MasterProject
# _ShuGenAI_


## This is instructions how to run this application.

### Required hardware to run this project:
 - Nvidia GPU(GTX10-series or newer)
 - Minimum 16Gb RAM
 - Intel Core i3/Ryzen 3 or higher

### Required software to run this project:
 - Ubuntu Linux or another Linux distribution
 - Nvidia Container Toolkit
 - Docker
 - Docker-Compose



### First of all You need to fill .env file with Your data:

### _Project configuration_
>DJANGO_SECRET_KEY - Put there Your secret key. In most cases it's a random string.
> 
>DJANGO_DEBUG - Allow You to see debug messages on errors. 
> 
>USE_MOCK_OUTPUT - This is mock AI features output. If You haven't API key for [AI/ML](aimlapi.com) set to True.

### _Database configuration_
>POSTGRES_DB - Here provide Your database name.
> 
>POSTGRES_USER - Here provide Your database user.
> 
>POSTGRES_PASSWORD - Here provide Your database password.
> 
>(If You run project on localhost for testing set variables above to `postgres`).
>
>POSTGRES_HOST - Do not change without need
> 
>POSTGRES_PORT - Do not change without need

### _Email configuration_
> In app used `GMAIL` provider.
> 
>EMAIL_HOST_USER - Here provide Your email address.
> 
>EMAIL_HOST_PASSWORD - Here provide Your app password. 

### _AI API configuration_
>AI_API_KEY - Here provide Your API key for [AI/ML](aimlapi.com)

### Starting of application
In some cases You'll have to run commands with `sudo`.
### _For first start use_
```sh
docker-compose up --build
```

### _For next times_
```sh
docker-compose up
```

### _To stop containers_
```sh
docker-compose down
```

### _To stop containers with deleting volumes(data)_
```sh
docker-compose down -v
```