#!/usr/bin/R
#setwd("~/Downloads/csgo_hltv_glicko2/")
set.seed(1337)
# implement glicko2 rating (for steps s. Glickman (2013) http://www.glicko.net/glicko/glicko2.pdf)

## step 1 
# defaults for player/team variables (r, RD, sigma)
kr <- 1500  # default player rating
kRD <- 350  # default rating deviation
ksigma <- 0.06  # default volatility
# random value for tau from reasonable range (s. Glickman (2013)) decide later..
ktau <- sample(seq(0.3, 1.2, 0.1), 1)  # system constant for volatility
kepsilon <- 1e-6  # only for optimization

## step 2
#' Convert rating r to mu on Glicko-2 scale.
#' 
#' @param r a numeric vector of ratings.
#' @return The numeric vector of ratings on Glicko-2 scale.
#' @examples
#' GetMu(c(1500, 1200, 2000))
GetMu <- function(r) {
  (r - 1500) / 173.7178
}

#' Convert rating deviation RD to phi on Glicko-2 scale.
#' 
#' @param RD a numeric vector of rating deviations.
#' @return The numeric vector of rating deviations on Glicko-2 scale.
#' @examples
#' GetPhi(c(350, 650, 150))
GetPhi <- function(RD) {
  RD / 173.7178
}

## step 3
#' Get g(phi) for computing nu.
#' 
#' @param phi a numeric vector of rating deviations on Glicko-2 scale.
#' @return The numeric vector of g(phi).
#' @examples
#' GetG(GetPhi(c(350, 650, 150)))
GetG <- function(phi) {
  1 / sqrt(1 + (3 * phi^2) / pi^2)
}

#' Get Expected value E(mu, mu.op, phi.op) for computing nu.
#' 
#' @param mu a numeric value of a players/teams rating on Glicko-2 scale.
#' @param mu.op a numeric vector of opponents players/teams ratings the length of opponents on Glicko-2 scale.
#' @param phi.op a numeric vector of opponents players/teams rating deviations the length of opponents on Glicko-2 scale.
#' @return The numeric vector of E(mu, mu_j, phi_j).
#' @examples
#' # for three opponents:
#' GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150)))
GetE = function(mu, mu.op, phi.op) {
  1 / (1 + exp(-GetG(phi.op) * (mu - mu.op)))
}

#' Get quantity nu.
#' 
#' @param E.op a numeric vetor of expected values E(mu, mu.op, phi.op) the length of opponents on Glicko-2 scale.
#' @param g.op a numeric vetor of g(phi.op) the length of opponents on Glicko-2 scale.
#' @return The numeric value of the quantity nu.
#' @examples
#' # for three opponents:
#' GetNu(GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), GetG(GetPhi(c(350, 650, 150))))
GetNu <- function(E.op, g.op) {
  1 / sum(g.op^2 * E.op * (1 - E.op))
}

## step 4
#' Get quantity Delta.
#' 
#' @param nu a numeric value of the quantity nu.
#' @param E.op a numeric vetor of expected values E(mu, mu.op, phi.op) the length of opponents on Glicko-2 scale.
#' @param g.op a  numeric vetor of g(phi.op) the length of opponents on Glicko-2 scale.
#' @param s.op a numeric vetor of results s.op coded as (1 = win, 0 = loss, 0.5 = draw) the length of opponents.
#' @return The numeric value of the quantity Delta.
#' @examples
#' # for three opponents:
#' GetDelta(nu = GetNu(GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), GetG(GetPhi(c(350, 650, 150)))),
#' E.op = GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), 
#' g.op = GetG(GetPhi(c(350, 650, 150))),
#' s.op = c(1, 0, 1))
GetDelta <- function(nu, E.op, g.op, s.op) {
  nu * sum(g.op * (s.op - E.op))
}

## step 5
#' Get value of helper function f(x).
#' 
#' @param x a numeric value.
#' @param sigma a numeric value of the rating volatility on the Glicko-2 scale.
#' @param phi a numeric value of the rating deviation on the Glicko-2 scale.
#' @param Delta a numeric value of quantity Delta.
#' @param nu a numeric value of the quantity nu.
#' @param tau a numeric value of the system constant tau.
#' @return The numeric value of the helper function x.
#' @examples
#' # for three opponents:
#' nu <- GetNu(GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), GetG(GetPhi(c(350, 650, 150))))
#' Delta <- GetDelta(nu = nu,
#' E.op = GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), 
#' g.op = GetG(GetPhi(c(350, 650, 150))),
#' s.op = c(1, 0, 1))
#' GetFxHelper(log(ksigma^2), ksigma, GetPhi(kRD), Delta, nu, ktau)
GetFxHelper <- function(x, sigma, phi, Delta, nu, tau) {
  f <- (exp(x) * (Delta^2 - phi^2 - nu - exp(x)) / (2 * (phi^2 + nu + exp(x))^2)) - ((x - log(sigma^2)) / tau^2)
  return(f)
}

# for three opponents:
# nu <- GetNu(GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), GetG(GetPhi(c(350, 650, 150))))
# Delta <- GetDelta(nu = nu,
# E.op = GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), 
# g.op = GetG(GetPhi(c(350, 650, 150))),
# s.op = c(1, 0, 1))
# GetFxHelper(log(ksigma^2), ksigma, GetPhi(kRD), Delta, nu, ktau)


#' Get the updated value of sigma: sigma.new.
#' 
#' @param sigma a numeric value of the rating volatility on the Glicko-2 scale.
#' @param phi a numeric value of the rating deviation on the Glicko-2 scale.
#' @param Delta a numeric value of quantity Delta.
#' @param nu a numeric value of the quantity nu.
#' @param tau a numeric value of the system constant tau.
#' @return The numeric value of the updated value of sigma.
#' @examples
#' # for three opponents:
#' nu <- GetNu(GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), GetG(GetPhi(c(350, 650, 150))))
#' Delta <- GetDelta(nu = nu,
#' E.op = GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), 
#' g.op = GetG(GetPhi(c(350, 650, 150))),
#' s.op = c(1, 0, 1))
#' GetSigmaNew(log(ksigma^2), ksigma, GetPhi(kRD), Delta, nu, ktau)
GetSigmaNew <- function(sigma, phi, Delta, nu, tau) {
  # 2
  A <- a <- log(sigma^2)
  if (Delta^2 > (phi^2 + nu)) {
    B <- log(Delta^2 - phi^2 - nu)
  } else {
    k <- 1
    while (GetFxHelper((a - k * tau), sigma, phi, Delta, nu, tau) < 0) {
      k <- k + 1
      # print(k)
    }
    B <- a - k * tau
  }
  # 3
  fA <- GetFxHelper(A, sigma, phi, Delta, nu, tau)
  fB <- GetFxHelper(B, sigma, phi, Delta, nu, tau)
  # 4
  while (abs(B - A) > kepsilon) {
    # print(abs(B - A))
    # a
    C <- A + (A - B) * fA / (fB - fA)
    fC <- GetFxHelper(C, sigma, phi, Delta, nu, tau)
    # b
    if ((fC * fB) < 0) {
      A <- B
      fA <- fB
    } else {
      fA <- fA / 2
    }
    # c
    B <- C
    fB <- fC
  }
  sigma.new <- exp(A/2)
  return(sigma.new)
}

# step 6
#' Get the updated value of phi to new pre-rating period: phi.pre.
#' 
#' @param phi a numeric value of the rating deviation on the Glicko-2 scale.
#' @param sigma.new a numeric value of the rating volatility on the Glicko-2 scale.
#' @return The numeric value of the updated value of phi to new pre-rating period.
#' @examples
#' # for three opponents:
#' nu <- GetNu(GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), GetG(GetPhi(c(350, 650, 150))))
#' Delta <- GetDelta(nu = nu,
#' E.op = GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), 
#' g.op = GetG(GetPhi(c(350, 650, 150))),
#' s.op = c(1, 0, 1))
#' sigma.new <- GetSigmaNew(log(ksigma^2), ksigma, GetPhi(kRD), Delta, nu, ktau)
#' GetPhiPre(GetPhi(kRD), sigma.new)
GetPhiPre <- function(phi, sigma.new) {
  sqrt(phi^2 + sigma.new^2)
}

# step 7
#' Get the updated value of phi: phi.new.
#' 
#' @param phi a numeric value of the rating deviation on the Glicko-2 scale.
#' @param sigma.new a numeric value of the rating volatility on the Glicko-2 scale.
#' @return The numeric value of the updated value of phi phi.new.
#' @examples
#' # for three opponents:
#' nu <- GetNu(GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), GetG(GetPhi(c(350, 650, 150))))
#' Delta <- GetDelta(nu = nu,
#' E.op = GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), 
#' g.op = GetG(GetPhi(c(350, 650, 150))),
#' s.op = c(1, 0, 1))
#' sigma.new <- GetSigmaNew(log(ksigma^2), ksigma, GetPhi(kRD), Delta, nu, ktau)
#' phi.pre <- GetPhiPre(GetPhi(kRD), sigma.new)
#' GetPhiNew(GetPhi(kRD), sigma.new, nu)
GetPhiNew <- function(phi.pre, sigma.new, nu) {
  1 / sqrt(1 / phi.pre^2 + 1 / nu)
}

#' Get the updated value of mu: mu.new.
#' 
#' @param mu a numeric value of the rating on the Glicko-2 scale.
#' @param phi.new a numeric value of the rating volatility on the Glicko-2 scale.
#' @param nu a numeric value of the quantity nu.
#' @param Delta a numeric value of quantity Delta.
#' @return The numeric value of the updated value of mu mu.new.
#' @examples
#' # for three opponents:
#' nu <- GetNu(GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), GetG(GetPhi(c(350, 650, 150))))
#' Delta <- GetDelta(nu = nu,
#' E.op = GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), 
#' g.op = GetG(GetPhi(c(350, 650, 150))),
#' s.op = c(1, 0, 1))
#' sigma.new <- GetSigmaNew(log(ksigma^2), ksigma, GetPhi(kRD), Delta, nu, ktau)
#' phi.pre <- GetPhiPre(GetPhi(kRD), sigma.new)
#' phi.new <- GetPhiNew(GetPhi(kRD), sigma.new, nu)
#' GetMuNew(GetMu(kr), phi.new, nu, Delta)
GetMuNew <- function(mu, phi.new, nu, Delta) {
  mu + phi.new^2 * (Delta / nu)  # part in the brackets is the sum part
}

# step 8
#' Get the updated value of r: r.new.
#' 
#' @param mu.new a numeric value of the updated rating on the Glicko-2 scale.
#' @return The numeric value of the updated value of the rating r.
#' @examples
#' # for three opponents:
#' nu <- GetNu(GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), GetG(GetPhi(c(350, 650, 150))))
#' Delta <- GetDelta(nu = nu,
#' E.op = GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), 
#' g.op = GetG(GetPhi(c(350, 650, 150))),
#' s.op = c(1, 0, 1))
#' sigma.new <- GetSigmaNew(log(ksigma^2), ksigma, GetPhi(kRD), Delta, nu, ktau)
#' phi.pre <- GetPhiPre(GetPhi(kRD), sigma.new)
#' phi.new <- GetPhiNew(GetPhi(kRD), sigma.new, nu)
#' mu.new <- GetMuNew(GetMu(kr), phi.new, nu, Delta)
#' GetRNew(mu.new)
GetRNew <- function(mu.new) {
  173.7178 * mu.new + 1500
}

#' Get the updated value of RD: RD.new.
#' 
#' @param phi.new a numeric value of the updated rating deviation on the Glicko-2 scale.
#' @return The numeric value of the updated value of the rating RD.
#' @examples
#' # for three opponents:
#' nu <- GetNu(GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), GetG(GetPhi(c(350, 650, 150))))
#' Delta <- GetDelta(nu = nu,
#' E.op = GetE(GetMu(kr), GetMu(c(1500, 1200, 2000)), GetPhi(c(350, 650, 150))), 
#' g.op = GetG(GetPhi(c(350, 650, 150))),
#' s.op = c(1, 0, 1))
#' sigma.new <- GetSigmaNew(log(ksigma^2), ksigma, GetPhi(kRD), Delta, nu, ktau)
#' phi.pre <- GetPhiPre(GetPhi(kRD), sigma.new)
#' phi.new <- GetPhiNew(GetPhi(kRD), sigma.new, nu)
#' mu.new <- GetMuNew(GetMu(kr), phi.new, nu, Delta)
#' GetRDNew(phi.new)
GetRDNew <- function(phi.new) {
  173.7178 * phi.new
}

## Final Step: Function for Everything

#' Get the Glicko2Rating of a player.
#' 
#' @param r a numeric value of the players current rating.
#' @param RD a numeric value of the players current rating deviation.
#' @param sigma a numeric value of the players volatility.
#' @param r.op a numeric vector of the opponents current ratings of arbitraty length m.
#' @param RD.op a numeric vector of the opponents current rating deviations of arbitraty length m.
#' @param s.op a numeric vetor of results s.op coded as (1 = win, 0 = loss, 0.5 = draw) of arbitraty length m.
#' @param tau a numeric value of the system constant.
#' @param kepsilon an numeric value used for convergence.
#' @return The numeric value of the updated value of the rating RD.
GetGlicko2Rating <- function(r = 1500, RD = 350, sigma = 0.06, r.op, RD.op, s.op, tau = 0.5, kepsilon = 1e-6) {
  # player
  mu <- GetMu(r)
  phi <- GetPhi(RD)
  
  if (length(s.op) > 0) {
    # opponents
    mu.op <- GetMu(r.op)
    phi.op <- GetPhi(RD.op)
    g.op <- GetG(phi.op)
    E.op <- GetE(mu, mu.op, phi.op)
    
    # calculate quantities for computation
    nu <- GetNu(E.op, g.op)
    Delta <- GetDelta(nu, E.op, g.op, s.op)
    
    # updates
    sigma.new <- GetSigmaNew(sigma, phi, Delta, nu, tau)
    phi.pre <- GetPhiPre(phi, sigma.new)
    phi.new <- GetPhiNew(phi.pre, sigma.new, nu)
    mu.new <- GetMuNew(mu, phi.new, nu, Delta)
    
    # convert
    r.new <- GetRNew(mu.new)
    RD.new <- GetRDNew(phi.new)
    
    # result
    result <- list(r = r, RD = RD, sigma = sigma, r.new = r.new, RD.new = RD.new, sigma.new = sigma.new)
    
  } else {
    phi.new <- sqrt(phi^2 + sigma^2)
    RD.new <- GetRDNew(phi.new)
    # result
    result <- list(r = r, RD = RD, sigma = sigma, r.new = r, RD.new = RD.new, sigma.new = sigma)
  }
  return(result)
  
}

## TEST (s. Glickman (2013)) ##

## SETUP
# initial rating
e.r <- 1500
# initial rating deviation
e.RD <- 200
# initial volatility
e.sigma <- 0.06

# opponents ratings
e.r.op <- c(1400, 1550, 1700)
# opponents rating deviations
e.RD.op <- c(30, 100, 300)
# results
e.s.op <- c(1, 0, 0)  # win, loss, loss

# system constant
e.tau <- 0.5

## CALCULATIONS
GetGlicko2Rating(e.r, e.RD, e.sigma, e.r.op, e.RD.op, e.s.op, 0.5, 1e-6)

## STEP BY STEP
# player
e.mu <- GetMu(e.r)
e.phi <- GetPhi(e.RD)

# opponents (check with table table by column)
e.mu.op <- GetMu(e.r.op)
e.phi.op <- GetPhi(e.RD.op)
e.g.op <- GetG(e.phi.op)
e.E.op <- GetE(e.mu, e.mu.op, e.phi.op)
e.s.op

# calculate quantities for computation
e.nu <- GetNu(e.E.op, e.g.op)
e.Delta <- GetDelta(e.nu, e.E.op, e.g.op, e.s.op)

# checks on helper function
e.A <- e.a <- log(0.06^2)
e.B <- e.a - e.tau
GetFxHelper(e.A, e.sigma, e.phi, e.Delta, e.nu, e.tau)
GetFxHelper(e.B, e.sigma, e.phi, e.Delta, e.nu, e.tau)

# updates
e.sigma.new <- GetSigmaNew(e.sigma, e.phi, e.Delta, e.nu, e.tau)
e.phi.pre <- GetPhiPre(e.phi, e.sigma.new)
e.phi.new <- GetPhiNew(e.phi.pre, e.sigma.new, e.nu)
e.mu.new <- GetMuNew(e.mu, e.phi.new, e.nu, e.Delta)

# convert
e.r.new <- GetRNew(e.mu.new)
e.RD.new <- GetRDNew(e.phi.new)


## TEST 2: Scaling
# opponents ratings
n.op <- 100000  # number of Opponents
e.r.op <- rnorm(n.op, 1500, 400)
# opponents rating deviations
e.RD.op <- runif(n.op, 40, 500)
# results
e.s.op <- sample(0:1, n.op, replace = TRUE, prob = c(1, 5))  # win, loss, loss
# system constant
e.tau <- 0.5

## CALCULATIONS
system.time(rep(GetGlicko2Rating(e.r, e.RD, e.sigma, e.r.op, e.RD.op, e.s.op, 0.5, 1e-6), n.op))

