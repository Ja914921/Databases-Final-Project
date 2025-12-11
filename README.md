## Project Name 
GameSearch

## What is the goal of your project?
GameSearch is a mySQL-backed app that lets users create accounts, search for video games by title and different filters, view different analytics such as top 10 games in sales and ESRB ratings, and log out as well. I use datasets from Kaggle to import information (Video Game Sales Dataset) ( Video Game ESRB Rating Dataset) (Metacritic Game Scores Dataset)

## What interaction does your app provide?
- login / create new accounts: login window appears before GUI. This screen allows for creation of new users or allows users to log into their accounts they made in the past
- User management: users can delete their accounts after confirming their account
- Game Search: Searches games with different filters (title, release year, genre, platform)
- Analytic Views: top N best selling games by global sales, Sales by ESRB ratings


## Video recording
finalprojectvid.mp4
logoutvid.mp4
## ER diagram design of your app
databaseFinalTable.png

## How to run code
git clone https://github.com/Ja914921/Databases-Final-Project

mysql --local-infile=1 -u root -p < databaseFinal.sql

python GUIApp.py
