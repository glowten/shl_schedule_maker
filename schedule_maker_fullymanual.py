import numpy as np
import pandas as pd
import copy
import math
import argparse

debug_enabled = False

def debug_print(*printables):
    if debug_enabled:
        print(*printables)

def rotate_robin(rotating_teams):
    return [rotating_teams[0]] + [rotating_teams[-1]] + rotating_teams[1:-1]

def _real_round_robin(teams: list, double_round_robin: bool) -> list[list]:
    rotating_teams = copy.deepcopy(teams)
    full_rotations = len(teams) - 1
    if double_round_robin:
        full_rotations = full_rotations * 2
    rounds = []
    for round_num in range(full_rotations):
        curr_round = []
        for i in range(len(rotating_teams) // 2):
            if round_num % 2 == 0:
                curr_round.append([rotating_teams[i], rotating_teams[-(i + 1)]])
            else:
                curr_round.append([rotating_teams[-(i + 1)], rotating_teams[i]])
        rounds.append(curr_round)
        rotating_teams = rotate_robin(rotating_teams)
    return rounds

# def _swap_round_robin_order(teams: list) -> list:
#     # make it so that home/away order is the opposite of what comes out of an unswapped round robin with this team order
#     # also makes it so matchups are reversed from original round robin (so we can alternate the first halves of rounds between round robins and maintain one/off sched)
#     # (a b c d) -> (h g f e)
#     # (e f g h) -> (d c b a)
#     # should we maybe shift by one to avoid repeating matchups every week?

#     # rotating_teams = copy.deepcopy(teams)
#     # halfway = len(rotating_teams) // 2
#     # return list(reversed(rotating_teams[halfway:])) + list(reversed(rotating_teams[:halfway]))
#     return teams[-1:] + teams[:-1]

# def _incorrect_round_robin(teams: list, double_round_robin: bool) -> list[list]:
#     # one cycle of teams (circle), imagine as circle being squished and slid along one at a time like a bike chain
#     rotating_teams = copy.deepcopy(teams)
#     halfway = len(rotating_teams) // 2
#     rounds = []
#     total_rounds = 2 * len(rotating_teams) if double_round_robin else len(rotating_teams)
#     # if single round robin, half games for any given team will be at home and half will be away
#     # one home one away game against each other team

#     # (a b c d) -> (e a b c) -> (f e a b) -> (g f e a) -> (h g f e) -> (d h g f) -> (c d h g) -> (b c d h) (DONE) -> (a b c d)
#     # (e f g h) -> (f g h d) -> (g h d c) -> (h d c b) -> (d c b a) -> (c b a e) -> (b a e f) -> (a e f g) (DONE) -> (e f g h)

#     for round in range(total_rounds):
#         curr_round = []
#         debug_print(rotating_teams[:halfway])
#         debug_print(rotating_teams[halfway:])
#         for matchup in range(halfway):
#             curr_round.append([rotating_teams[matchup], rotating_teams[halfway + matchup]])
#         debug_print('matchups')
#         debug_print(curr_round)
#         debug_print()
#         rounds.append(curr_round)
#         rotating_teams = [rotating_teams[halfway]] + rotating_teams[:halfway - 1] + rotating_teams[halfway + 1:] + [rotating_teams[halfway - 1]]
#         # this could also be done by just doing teams[matchup] vs teams[-matchup] and sliding entire array
#     return rounds

def _rotating_wheels(home_teams: list, away_teams: list, reverse_home_away=False):
    stationary_home_teams = copy.deepcopy(home_teams)
    rotating_away_teams = copy.deepcopy(away_teams)
    halfway = len(away_teams)
    total_rounds = len(rotating_away_teams)
    rounds = []
    for round in range(total_rounds):
        curr_round = []
        debug_print(stationary_home_teams)
        debug_print(rotating_away_teams)
        for matchup in range(halfway):
            if reverse_home_away:
                curr_round.append([rotating_away_teams[matchup], stationary_home_teams[matchup]])
            else:
                curr_round.append([stationary_home_teams[matchup], rotating_away_teams[matchup]])
        rounds.append(curr_round)
        debug_print('matchups')
        debug_print(curr_round)
        debug_print()
        rotating_away_teams = [rotating_away_teams[-1]] + rotating_away_teams[:-1]
    return rounds

def _format_round(round, curr_total_day):
    out = []
    for match in round:
        out.append(pd.DataFrame({'day_int': [curr_total_day], 'home': [match[0]], 'away': [match[1]]}))
    return pd.concat(out)

def make_schedule_arbitrary(east_teams, west_teams, league):
    # shl: play each team in conference 4 times (4 x 11)
    #      then play each team outside of conference max of 2 times (2 x 10 + 1 x 2)
    # smjhl: play each team in conference 6 times (6 x 7)
    #        then play each team outside of conference 3 times (3 x 8)
    east_shuffled_2 = list(np.random.permutation(east_teams))
    east_shuffled_3 = list(np.random.permutation(east_teams))
    west_shuffled_2 = list(np.random.permutation(west_teams))
    west_shuffled_3 = list(np.random.permutation(west_teams))


    if league == 'shl':
        # 9 day rotation
        day_rotation = 9
        
        schedule_out = []

        east_rr1 = _real_round_robin(east_teams, double_round_robin=True)

        east_rr2 = _real_round_robin(east_shuffled_2, double_round_robin=True)

        west_rr1 = _real_round_robin(west_teams, double_round_robin=True)

        west_rr2 = _real_round_robin(west_shuffled_2, double_round_robin=True)

        cross_rr1 = _rotating_wheels(east_teams, west_teams)

        cross_rr2 = _rotating_wheels(west_teams, east_teams)

        # this skips the last round of round robin so we get 2 x 10 and 1 x 2
        num_initial_rounds = len(cross_rr1) - 1
        
        even_round = True
        curr_total_day = -1
        for curr_round in range(num_initial_rounds):
            east_rr1_round = east_rr1.pop(0)
            west_rr1_round = west_rr1.pop(0)
            east_rr2_round = east_rr2.pop(0)
            west_rr2_round = west_rr2.pop(0)
            cross_rr_day5 = cross_rr1.pop(0)
            cross_rr_day6 = cross_rr2.pop(0)
            for curr_day in range(day_rotation):
                curr_total_day += 1
                if curr_day == 0:
                    schedule_out.append(_format_round(east_rr1_round, curr_total_day))
                if curr_day == 1:
                    schedule_out.append(_format_round(west_rr1_round, curr_total_day))
                if curr_day == 2:
                    schedule_out.append(_format_round(east_rr2_round, curr_total_day))
                if curr_day == 3:
                    schedule_out.append(_format_round(west_rr2_round, curr_total_day))
                if curr_day == 4:
                    continue
                if curr_day == 5:
                    schedule_out.append(_format_round(cross_rr_day5, curr_total_day))
                if curr_day == 6:
                    continue
                if curr_day == 7:
                    schedule_out.append(_format_round(cross_rr_day6, curr_total_day))
                if curr_day == 8:
                    continue
            even_round = not even_round
        num_remaining_rounds = len(east_rr1)
        day_rotation = 5
        for curr_round in range(num_remaining_rounds):
            east_rr1_round = east_rr1.pop(0)
            west_rr1_round = west_rr1.pop(0)
            east_rr2_round = east_rr2.pop(0)
            west_rr2_round = west_rr2.pop(0)
            # for the last round, spread out games in the last 2 days so that it's not all east games on the second last day and all west games on last day
            last_round = curr_round + 1 >= num_remaining_rounds
            halfway = len(east_rr2_round) // 2
            for curr_day in range(day_rotation):
                curr_total_day += 1
                if curr_day == 0:
                    schedule_out.append(_format_round(east_rr1_round, curr_total_day))
                if curr_day == 1:
                    schedule_out.append(_format_round(west_rr1_round, curr_total_day))
                # leave open day mid week as buffer for the east west final day shuffle
                if curr_day == 2:
                    continue
                if curr_day == 3:
                    if last_round:
                        schedule_out.append(_format_round(east_rr2_round[:halfway] + west_rr2_round[:halfway], curr_total_day))
                    else:
                        schedule_out.append(_format_round(east_rr2_round, curr_total_day))
                if curr_day == 4:
                    if last_round:
                        schedule_out.append(_format_round(east_rr2_round[halfway:] + west_rr2_round[halfway:], curr_total_day))
                    else:
                        schedule_out.append(_format_round(west_rr2_round, curr_total_day))

        debug_print('len remaining rounds')
        debug_print('east_rr1', len(east_rr1))
        debug_print('west_rr1', len(west_rr1))
        debug_print('east_rr2', len(east_rr2))
        debug_print('west_rr2', len(west_rr2))
        return pd.concat(schedule_out)
    elif league == 'smjhl':
        # smjhl: play each team in conference 6 times (6 x 7)
        #        then play each team outside of conference 3 times (3 x 8)
        # 9 day rotation
        day_rotation = 13
        
        schedule_out = []

        east_rr1 = _real_round_robin(east_teams, double_round_robin=True)

        east_rr2 = _real_round_robin(east_shuffled_2, double_round_robin=True)

        east_rr3 = _real_round_robin(east_shuffled_3, double_round_robin=True)

        west_rr1 = _real_round_robin(west_teams, double_round_robin=True)

        west_rr2 = _real_round_robin(west_shuffled_2, double_round_robin=True)

        west_rr3 = _real_round_robin(west_shuffled_3, double_round_robin=True)

        cross_rr1 = _rotating_wheels(east_teams, west_shuffled_2)

        cross_rr2 = _rotating_wheels(west_teams, east_shuffled_2)
        
        even_filter = np.arange(len(cross_rr2)) % 2 == 0
        odd_filter = np.arange(len(cross_rr2)) % 2 == 1
        cross_rr3 = list(np.array(_rotating_wheels(east_teams, west_shuffled_3))[even_filter]) + list(np.array(_rotating_wheels(east_teams, west_shuffled_3, reverse_home_away=True))[odd_filter])

        # this doesn't skip the last round of round robin so we get 3 x 8
        num_initial_rounds = len(cross_rr1)
        
        even_round = True
        curr_total_day = -1
        for curr_round in range(num_initial_rounds):
            east_rr1_round = east_rr1.pop(0)
            west_rr1_round = west_rr1.pop(0)
            east_rr2_round = east_rr2.pop(0)
            west_rr2_round = west_rr2.pop(0)
            east_rr3_round = east_rr3.pop(0)
            west_rr3_round = west_rr3.pop(0)
            cross_rr_day5 = cross_rr1.pop(0)
            cross_rr_day6 = cross_rr2.pop(0)
            cross_rr_day7 = cross_rr3.pop(0)
            for curr_day in range(day_rotation):
                curr_total_day += 1
                if curr_day == 0:
                    schedule_out.append(_format_round(east_rr1_round, curr_total_day))
                if curr_day == 1:
                    schedule_out.append(_format_round(west_rr1_round, curr_total_day))
                if curr_day == 2:
                    schedule_out.append(_format_round(east_rr2_round, curr_total_day))
                if curr_day == 3:
                    schedule_out.append(_format_round(west_rr2_round, curr_total_day))
                if curr_day == 4:
                    schedule_out.append(_format_round(east_rr3_round, curr_total_day))
                if curr_day == 5:
                    schedule_out.append(_format_round(west_rr3_round, curr_total_day))
                if curr_day == 6:
                    continue
                if curr_day == 7:
                    schedule_out.append(_format_round(cross_rr_day5, curr_total_day))
                if curr_day == 8:
                    continue
                if curr_day == 9:
                    schedule_out.append(_format_round(cross_rr_day6, curr_total_day))
                if curr_day == 10:
                    continue
                if curr_day == 11:
                    schedule_out.append(_format_round(cross_rr_day7, curr_total_day))
                if curr_day == 12:
                    continue
            even_round = not even_round
        num_remaining_rounds = len(east_rr1)
        day_rotation = 7
        for curr_round in range(num_remaining_rounds):
            east_rr1_round = east_rr1.pop(0)
            west_rr1_round = west_rr1.pop(0)
            east_rr2_round = east_rr2.pop(0)
            west_rr2_round = west_rr2.pop(0)
            east_rr3_round = east_rr3.pop(0)
            west_rr3_round = west_rr3.pop(0)
            # for the last round, spread out games in the last 2 days so that it's not all east games on the second last day and all west games on last day
            last_round = curr_round + 1 >= num_remaining_rounds
            halfway = len(east_rr2_round) // 2
            for curr_day in range(day_rotation):
                curr_total_day += 1
                if curr_day == 0:
                    schedule_out.append(_format_round(east_rr1_round, curr_total_day))
                if curr_day == 1:
                    schedule_out.append(_format_round(west_rr1_round, curr_total_day))
                if curr_day == 2:
                    schedule_out.append(_format_round(east_rr3_round, curr_total_day))
                if curr_day == 3:
                    schedule_out.append(_format_round(west_rr3_round, curr_total_day))
                # leave open day mid week as buffer for the east west final day shuffle
                if curr_day == 4:
                    continue
                if curr_day == 5:
                    if last_round:
                        schedule_out.append(_format_round(east_rr2_round[:halfway] + west_rr2_round[:halfway], curr_total_day))
                    else:
                        schedule_out.append(_format_round(east_rr2_round, curr_total_day))
                if curr_day == 6:
                    if last_round:
                        schedule_out.append(_format_round(east_rr2_round[halfway:] + west_rr2_round[halfway:], curr_total_day))
                    else:
                        schedule_out.append(_format_round(west_rr2_round, curr_total_day))

        debug_print('len remaining rounds')
        debug_print('east_rr1', len(east_rr1))
        debug_print('west_rr1', len(west_rr1))
        debug_print('east_rr2', len(east_rr2))
        debug_print('west_rr2', len(west_rr2))
        return pd.concat(schedule_out)

def transform_schedule_dates(schedule, start_date='2052-10-04'):
    start_date = pd.to_datetime(start_date)
    schedule = copy.deepcopy(schedule)
    schedule['date'] = schedule.apply(lambda x: start_date + pd.Timedelta(days=x.day_int), axis=1)
    return schedule[['date', 'day_int', 'home', 'away']]


# testing / visualization
def show_home_away_balance(schedule, teams):
    for team in teams:
        debug_print()
        home = list(schedule[schedule['home'] == team].day_int)
        debug_print('home days', team, home)
        debug_print('len home', len(home))
        away = list(schedule[schedule['away'] == team].day_int)
        debug_print('away days', team, away)
        debug_print('len away', len(away))
        all = list(schedule[(schedule['home'] == team) | (schedule['away'] == team)].day_int)
        debug_print('all', team, all)
        debug_print('len all', len(all))

def show_matchups(schedule, team):
    debug_print()
    debug_print(team)
    all = schedule[(schedule['home'] == team) | (schedule['away'] == team)]
    pd.set_option('display.max_rows', 500)
    debug_print(all)

def show_num_games_per_month(dated_schedule):
    dated_schedule['year_month'] = dated_schedule.apply(lambda x: f"{x['date'].year}_{x['date'].month}", axis=1)

    homes = []
    for team in dated_schedule['home'].unique():
        team_homes = dated_schedule[dated_schedule['home'] == team][['year_month', 'date']]
        team_homes = team_homes.groupby(['year_month']).count().cumsum()
        team_homes = team_homes.reset_index()
        team_homes['home'] = team
        homes.append(team_homes)
    homes = pd.concat(homes)
    homes = pd.pivot_table(homes, values='date', index='home', columns='year_month')
    debug_print('homes')
    debug_print(homes)

    aways = []
    for team in dated_schedule['away'].unique():
        team_aways = dated_schedule[dated_schedule['away'] == team][['year_month', 'date']]
        team_aways = team_aways.groupby(['year_month']).count().cumsum()
        team_aways = team_aways.reset_index()
        team_aways['away'] = team
        aways.append(team_aways)
    aways = pd.concat(aways)
    aways = pd.pivot_table(aways, values='date', index='away', columns='year_month')
    debug_print('aways')
    debug_print(aways)
    
    all = []
    for team in dated_schedule['away'].unique():
        team_all = dated_schedule[(dated_schedule['home'] == team) | (dated_schedule['away'] == team)][['year_month', 'date']]
        team_all = team_all.groupby(['year_month']).count().cumsum()
        team_all = team_all.reset_index()
        team_all['all'] = team
        all.append(team_all)
    all = pd.concat(all)
    all = pd.pivot_table(all, values='date', index='all', columns='year_month')
    debug_print('all')
    debug_print(all)

# utility
def convert_day_schedule_to_fhm_schedule(day_schedule):
    day_schedule['YEAR'] = day_schedule['date'].dt.year
    day_schedule['MONTH'] = day_schedule['date'].dt.month
    day_schedule['DAY'] = day_schedule['date'].dt.day
    day_schedule['TEAM HOME'] = day_schedule['home']
    day_schedule['TEAM AWAY'] = day_schedule['away']
    day_schedule['GAME TYPE'] = 'Regular'
    day_schedule = day_schedule.sort_values('day_int')

    return day_schedule[['YEAR', 'MONTH', 'DAY', 'TEAM HOME', 'TEAM AWAY', 'GAME TYPE']]

def calc_game_matrix(day_schedule, teams):
    # Build a symmetric matrix of total games between each pair of teams
    team_list = list(teams)
    mat = pd.DataFrame(0, index=team_list, columns=team_list, dtype=int)

    # Support either raw schedule (home/away) or converted (TEAM HOME/TEAM AWAY)
    if 'home' in day_schedule.columns and 'away' in day_schedule.columns:
        home_col, away_col = 'home', 'away'
    elif 'TEAM HOME' in day_schedule.columns and 'TEAM AWAY' in day_schedule.columns:
        home_col, away_col = 'TEAM HOME', 'TEAM AWAY'
    else:
        raise ValueError("Schedule must contain either ('home','away') or ('TEAM HOME','TEAM AWAY') columns.")

    # Iterate through games and increment both [home,away] and [away,home]
    for h, a in day_schedule[[home_col, away_col]].itertuples(index=False):
        if h not in mat.index or a not in mat.columns:
            # Skip games with teams not in the provided list (if any)
            continue
        mat.at[h, a] += 1
        mat.at[a, h] += 1
    # change names to abbreviations for easier visualization
    return mat.rename(index={t: ''.join([a[0] for a in t.split()]) for t in team_list}, columns={t: ''.join([a[0] for a in t.split()]) for t in team_list})

# tests
def test_team_num_games(out_sched, east_teams, west_teams, league):
    # shl: 4 games in conference, max 2 games out (2 x 10, 1 x 2), 66 total, 33 home, 33 away
    # smjhl: 6 games in conference, 3 games out, 66 total, 33 home, 33 away
    # no back to backs
    if league == 'shl':
        for t in east_teams:
            home_games = out_sched[out_sched['TEAM HOME'] == t]
            away_games = out_sched[out_sched['TEAM AWAY'] == t]
            assert len(home_games) == 33
            assert len(away_games) == 33
            assert len(home_games) + len(away_games) == 66
            for other_east in east_teams:
                if other_east == t:
                    continue
                home_against = home_games[home_games['TEAM AWAY'] == other_east]
                away_against = away_games[away_games['TEAM HOME'] == other_east]
                assert len(home_against) == 2
                assert len(away_against) == 2
            for w in west_teams:
                home_against = home_games[home_games['TEAM AWAY'] == w]
                away_against = away_games[away_games['TEAM HOME'] == w]
                assert len(home_against) + len(away_against) <= 2
        for t in west_teams:
            home_games = out_sched[out_sched['TEAM HOME'] == t]
            away_games = out_sched[out_sched['TEAM AWAY'] == t]
            assert len(home_games) == 33
            assert len(away_games) == 33
            assert len(home_games) + len(away_games) == 66
            for other_west in west_teams:
                if other_west == t:
                    continue
                home_against = home_games[home_games['TEAM AWAY'] == other_west]
                away_against = away_games[away_games['TEAM HOME'] == other_west]
                assert len(home_against) == 2
                assert len(away_against) == 2
            for e in east_teams:
                home_against = home_games[home_games['TEAM AWAY'] == e]
                away_against = away_games[away_games['TEAM HOME'] == e]
                assert len(home_against) + len(away_against) <= 2
    if league == 'smjhl':
        for t in east_teams:
            home_games = out_sched[out_sched['TEAM HOME'] == t]
            away_games = out_sched[out_sched['TEAM AWAY'] == t]
            debug_print(t, len(home_games))
            assert len(home_games) == 33
            assert len(away_games) == 33
            assert len(home_games) + len(away_games) == 66
            for other_east in east_teams:
                if other_east == t:
                    continue
                home_against = home_games[home_games['TEAM AWAY'] == other_east]
                away_against = away_games[away_games['TEAM HOME'] == other_east]
                assert len(home_against) == 3
                assert len(away_against) == 3
            for w in west_teams:
                home_against = home_games[home_games['TEAM AWAY'] == w]
                away_against = away_games[away_games['TEAM HOME'] == w]
                assert len(home_against) + len(away_against) == 3
        for t in west_teams:
            home_games = out_sched[out_sched['TEAM HOME'] == t]
            away_games = out_sched[out_sched['TEAM AWAY'] == t]
            debug_print(t, len(home_games))
            assert len(home_games) == 33
            assert len(away_games) == 33
            assert len(home_games) + len(away_games) == 66
            for other_west in west_teams:
                if other_west == t:
                    continue
                home_against = home_games[home_games['TEAM AWAY'] == other_west]
                away_against = away_games[away_games['TEAM HOME'] == other_west]
                assert len(home_against) == 3
                assert len(away_against) == 3
            for e in east_teams:
                home_against = home_games[home_games['TEAM AWAY'] == e]
                away_against = away_games[away_games['TEAM HOME'] == e]
                assert len(home_against) + len(away_against) == 3
    # back to backs
    for t in east_teams + west_teams:
        t_games = out_sched[(out_sched['TEAM HOME'] == t) | (out_sched['TEAM AWAY'] == t)]
        t_games['game_day'] = pd.to_datetime(t_games[['YEAR', 'MONTH', 'DAY']])
        t_games['rest_day'] = t_games['game_day'] + pd.Timedelta(days=1)
        # just check for intersection between game days and rest days. if there are any game days on rest days (game day + 1), then we have a back to back
        assert len(set(t_games['rest_day']).intersection(set(t_games['game_day']))) == 0
    print('tests passed')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='schedule maker for shl or smjhl (team lists from s86)'
    )
    parser.add_argument('--league', type=str, help='shl or smjhl')
    parser.add_argument('--season', type=int, help='season number as an integer')
    parser.add_argument('--debug_log', default=False, type=bool, help='whether to show debug output')
    args = parser.parse_args()
    if args.debug_log:
        debug_enabled = True

    shl_east_teams = [
        "New England Wolfpack", "Hamilton Steelhawks", "Philadelphia Forge",
        "Atlanta Inferno", "Baltimore Platoon", "Manhattan Rage",
        "Nashville Sound", "Montreal Patriotes", "Tampa Bay Barracuda",
        "Toronto North Stars", "Buffalo Stampede", "Cincinnati Six"
    ]
    shl_west_teams = [
        "Winnipeg Aurora", "Calgary Dragons", "Denver Glacier Guardians",
        "Los Angeles Panthers", "Minnesota Monarchs", "Chicago Syndicate",
        "Texas Renegades", "San Francisco Pride", "Edmonton Blizzard",
        "Madison Valkyries", "Seattle Argonauts", "New Orleans Specters"
    ]

    j_north_teams = [
        "Anchorage Armada", "Kelowna Knights", "Vancouver Whalers", 
        "Newfoundland Berserkers", "Yukon Malamutes", "Quebec City Citadelles", 
        "Thunder Bay Walleye", 	"Great Falls Grizzlies", 
    ]
    j_south_teams = [
	    "Maine Timber", "Colorado Raptors", "Detroit Falcons", 
        "St. Louis Scarecrows", "Carolina Kraken", "Nevada Battleborn", 
        "Ottawa Highlanders", "San Diego Tidal"
    ]
    
    if str(args.league).lower() == 'shl':
        east_teams = shl_east_teams
        west_teams = shl_west_teams
    elif str(args.league).lower() == 'smjhl':
        east_teams = j_north_teams
        west_teams = j_south_teams
    else:
        raise Exception(f'league not valid, must be shl or smjhl: {args.league}')

    east_teams = list(np.random.permutation(east_teams))
    west_teams = list(np.random.permutation(west_teams))

    schedule = make_schedule_arbitrary(east_teams=east_teams, west_teams=west_teams, league=args.league)
    debug_print(schedule)

    for team in east_teams[:3] + west_teams[:3]:
        show_matchups(schedule, team)

    # start year for s86 was 2052
    start_year_delta = args.season - 86
    assert start_year_delta >= 0
    start_year = 2052 + start_year_delta

    dated_schedule = transform_schedule_dates(schedule=schedule, start_date=f'{start_year}-10-04')
    debug_print(dated_schedule.tail())

    show_num_games_per_month(dated_schedule)

    debug_print(calc_game_matrix(dated_schedule, east_teams + west_teams))

    out_sched = convert_day_schedule_to_fhm_schedule(dated_schedule)
    test_team_num_games(out_sched, east_teams, west_teams, args.league)
    out_path = f'fullymanual_schedules/{args.league}_s{args.season}_sched.csv'
    out_sched.to_csv(out_path, index=False)
    print('saved to', out_path)

    # schedule_arr_home = []
    # for team in east_example_teams + west_example_teams:
    #     row = [team]
    #     other_teams = east_example_teams + west_example_teams
    #     for other_team in other_teams:
    #         row.append(len(schedule[(schedule['home'] == team) & (schedule['away'] == other_team)]))
    #     row = pd.DataFrame(columns=['team'] + other_teams, data=[row])
    #     schedule_arr_home.append(row)
    # schedule_arr_home = pd.concat(schedule_arr_home)
    # print('schedule matrix home')
    # print(schedule_arr_home)

    # schedule_arr_away = []
    # for team in east_example_teams + west_example_teams:
    #     row = [team]
    #     other_teams = east_example_teams + west_example_teams
    #     for other_team in other_teams:
    #         row.append(len(schedule[(schedule['away'] == team) & (schedule['home'] == other_team)]))
    #     row = pd.DataFrame(columns=['team'] + other_teams, data=[row])
    #     schedule_arr_away.append(row)
    # schedule_arr_away = pd.concat(schedule_arr_away)
    # print('schedule matrix away')
    # print(schedule_arr_away)

    # schedule_arr_all = []
    # for team in east_example_teams + west_example_teams:
    #     row = [team]
    #     other_teams = east_example_teams + west_example_teams
    #     for other_team in other_teams:
    #         row.append(len(schedule[((schedule['away'] == team) | (schedule['home'] == team)) & ((schedule['home'] == other_team) | (schedule['away'] == other_team))]))
    #     row = pd.DataFrame(columns=['team'] + other_teams, data=[row])
    #     schedule_arr_all.append(row)
    # schedule_arr_all = pd.concat(schedule_arr_all)
    # print('schedule matrix all')
    # print(schedule_arr_all)