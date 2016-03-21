#!/usr/bin/R
library(data.table)
library(plyr)
library(ggplot2)
#setwd("~/Downloads/csgo_hltv_glicko2/")
source("glicko2.R")

GetPOSIXctDate <- function(datestring) {
  as.POSIXct(strptime(paste0(datestring, " 00:00:00"), "%Y-%m-%d %H:%M:%S"))
}

#load data (everything is interpreted as character by default because of quoting in csv)
hltv.data <- fread("hltv_org_matches_ 2014.csv", header = TRUE)

# format data
hltv.data$date <- as.POSIXct(strptime(hltv.data$date, "%d/%m %y"))
#hltv.data$month <- as.factor(format(hltv.data$date, "%Y-%m"))
hltv.data$map <- as.factor(hltv.data$map)
hltv.data$event <- as.factor(hltv.data$event)
hltv.data$team1 <- as.factor(gsub(" \\(\\d*\\)", "", hltv.data$team1))
hltv.data$team2 <- as.factor(gsub(" \\(\\d*\\)", "", hltv.data$team2))
hltv.data$matchid <- as.numeric(hltv.data$matchid)
hltv.data$teamid1 <- as.numeric(hltv.data$teamid1)
hltv.data$teamid2 <- as.numeric(hltv.data$teamid2)
hltv.data$eventid <- as.numeric(hltv.data$eventid)
hltv.data$score2 <- as.numeric(hltv.data$score2)
hltv.data$score1 <- as.numeric(hltv.data$score1)
str(hltv.data)

# score for team1 (0 = loss, 1 = win, 0.5 = draw)
hltv.data$score_code <- as.numeric(hltv.data$score1 > hltv.data$score2) + 0.5 * as.numeric(hltv.data$score1 == hltv.data$score2)

# summary of matches
summary(hltv.data)

#' Make an Update of Teams Ratings.
#' 
#' @param hltv.teamid a numeric teamid of a team from HLTV.org
#' @param hltv.start.period a POSIXct date of the start of a rating period. Currently only monthly periods supported. For
#' the rating period in (e.g. January 2015 as.POSIXct(strptime("2015-01-01 00:00:00", "%Y-%m-%d %H:%M:%S"))).
#' @param hltv.data a data.table containg the matches data.
#' @param hltv.ratings a data.table with ratings for all teams.
#' @return a data.table in format hltv.ratings with the updated values for team with specified hltv.teamid
UpdateHltvGlicko2Rating <- function(hltv.teamid, hltv.start.period, hltv.data, hltv.ratings, verbose = FALSE) {
  
  # get data in rating period
  #hltv.start.period <- as.POSIXct(strptime("2015-01-01 00:00:00", "%Y-%m-%d %H:%M:%S"))
  hltv.end.period <- seq(hltv.start.period, length = 2, by = "1 months")[2]  # eq. plus one month
  hltv.data.period <- hltv.data[date >= hltv.start.period & date < hltv.end.period, ]
  
  # teams statistics for Glicko-2
  hltv.r.team <- hltv.ratings[rate_date >= hltv.start.period & rate_date < hltv.end.period & teamid == hltv.teamid, ]$hltv_r
  hltv.RD.team <- hltv.ratings[rate_date >= hltv.start.period & rate_date < hltv.end.period & teamid == hltv.teamid, ]$hltv_RD
  hltv.sigma.team <- hltv.ratings[rate_date >= hltv.start.period & rate_date < hltv.end.period & teamid == hltv.teamid, ]$hltv_sigma
  
  # opponents statistics
  # vector of opponents
  hltv.op <- data.table(teamid = c(hltv.data.period[teamid1 == hltv.teamid, ]$teamid2, 
                                   hltv.data.period[teamid2 == hltv.teamid, ]$teamid1),
                        score = c(hltv.data.period[teamid1 == hltv.teamid, ]$score_code, 
                                  1 - hltv.data.period[teamid2 == hltv.teamid, ]$score_code))
  if (verbose == TRUE) {
    hltv.name.team <- unique(c(as.character(hltv.data[teamid2 == hltv.teamid, ]$team2), 
                               as.character(hltv.data[teamid1 == hltv.teamid, ]$team1)))
    cat(hltv.name.team, ":", nrow(hltv.op), "matches played", "in period\n")
  }
  
  # opponents ratings (data.table not capable of == for POSIXct)
  hltv.op.ratings <- hltv.ratings[rate_date >= hltv.start.period & rate_date < hltv.end.period, ]
  # join
  setkey(hltv.op, teamid)
  setkey(hltv.op.ratings, teamid)
  hltv.op.ratings <- hltv.op.ratings[hltv.op]
  
  # opponents statistics for Glicko-2
  hltv.r.op <- hltv.op.ratings$hltv_r
  hltv.RD.op <- hltv.op.ratings$hltv_RD
  #hltv.sigma.op <- hltv.op.ratings$hltv_sigma
  hltv.s.op <- hltv.op.ratings$score
  
  # get new Glicko-2 statistics
  hltv.glicko <- GetGlicko2Rating(hltv.r.team, hltv.RD.team, hltv.sigma.team, hltv.r.op, hltv.RD.op, hltv.s.op, 0.6, 1e-6)
  
  return(data.table(teamid = hltv.teamid, 
                    hltv_r = hltv.glicko$r.new, 
                    hltv_RD = hltv.glicko$RD.new, 
                    hltv_sigma = hltv.glicko$sigma.new,
                    hltv_maps = nrow(hltv.op),
                    hltv_score = sum(hltv.s.op),
                    rate_date = hltv.end.period))
}

# default values for Glicko-2
hltv.k.r <- 1500
hltv.k.RD <- 350
hltv.k.sigma <- 0.06

# get all unique teams
hltv.data.teams <- rbind(hltv.data[, list(team = team1, teamid = teamid1)], 
                         hltv.data[, list(team = team2, teamid = teamid2)])  # reshape
hltv.data.teams[, list(cnt = length(unique(team))), by = list(teamid)][order(cnt)]  # teamid:team = 1:1 relationship
hltv.data.teams <- unique(hltv.data.teams)  # all teams
hltv.data.n.teams <- nrow(hltv.data.teams)  # number of unique teams

# create initial rating table for each rating period
hltv.ratings <- data.table(teamid = hltv.data.teams$teamid, 
                           hltv_r = rep(hltv.k.r, hltv.data.n.teams),
                           hltv_RD = rep(hltv.k.RD, hltv.data.n.teams),
                           hltv_sigma = rep(hltv.k.sigma, hltv.data.n.teams),
                           hltv_maps = rep(0, hltv.data.n.teams),
                           hltv_score = rep(0, hltv.data.n.teams),
                           rate_date = rep(as.POSIXct(strptime("2014-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")), 
                                           hltv.data.n.teams))

system.time(for(period in (seq(GetPOSIXctDate("2014-01-01"), length = 23, by = "1 months"))) {
  # period is converted to numeric so re-convert it...
  period <- as.POSIXct(period, origin = "1970-01-01")
  
  # update Ratings
  hltv.ratings.new <- data.table(ldply(hltv.data.teams$teamid,
                                       UpdateHltvGlicko2Rating, 
                                       hltv.start.period = period,
                                       hltv.data = hltv.data,
                                       hltv.ratings = hltv.ratings))
  
  hltv.ratings <- rbind(hltv.ratings, hltv.ratings.new)
})



# join with to get teamname
hltv.maps <- hltv.ratings[, list(hltv_maps_total = sum(hltv_maps), 
                                 hltv_score_total = sum(hltv_score)),
                          by = list(teamid)]

setkey(hltv.maps, teamid)
setkey(hltv.data.teams, teamid)
setkey(hltv.ratings, teamid)
hltv.data.result <- hltv.maps[hltv.data.teams][hltv.ratings][order(-rate_date, -hltv_r)]

# restrict to teams with more than 50 observed maps and more than 5 maps played in a rating period
hltv.data.result <- hltv.data.result[hltv_maps_total > 50 & hltv_maps > 5, ]

# select top 20 at the last rating period
hltv.data.result.201512 <- hltv.data.result[format(rate_date, "%Y-%m") == "2015-12", ][order(-hltv_r)][1:20][, list(end_of_rating_period = rate_date, 
                                                                                                                    team, 
                                                                                                                    rating = hltv_r, 
                                                                                                                    rating_deviation = hltv_RD, 
                                                                                                                    volatitlity = hltv_sigma, 
                                                                                                                   total_maps = hltv_maps_total)]

# add number in ranking to teams name
hltv.data.result.201512$team <- paste0(seq(1:nrow(hltv.data.result.201512)),". ",hltv.data.result.201512$team)

# plot the results
ggplot(hltv.data.result.201512, aes(x = team, y = rating, colour = team)) + geom_point(stat = "identity") + 
  scale_x_discrete(limits = rev(hltv.data.result.201512$team)) +
  geom_errorbar(aes(ymin = rating - 2 * rating_deviation, ymax = rating + 2 * rating_deviation)) +
  coord_flip() + theme(legend.position = "none") + ylab("Rating via Glicko-2") + xlab("CS:GO Team")

