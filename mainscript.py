###############################################################################
#TEXAS HOLD'EM DEMO


#  - Custom pseudo-random generator (linear congruential)
#  - Full 52-card deck
#  - Shuffle & deal hole cards
#  - Evaluate 7-card best-5 hands with correct poker ranking
#  - Monte Carlo simulation to estimate chance of winning vs N opponents
#  - Ask user for an action each street, display final showdown
###############################################################################

# ----------------------------------------------------------------------------
# 1. PSEUDO-RANDOM (LCG)
# ----------------------------------------------------------------------------
_seed = 5674832  # A default seed; 

def rand_int(low, high):
    """
    Custom linear congruential generator to return an integer in [low, high].
    No built-in random used.
    """
    global _seed
    # LCG parameters (example constants)
    _seed = (1103515245 * _seed + 12345) % 2147483648
    r = _seed % (high - low + 1)
    return low + r

def shuffle_in_place(lst):
    """
    Fisher-Yates shuffle of a list in place, using our rand_int().
    """
    n = len(lst)
    for i in range(n - 1, 0, -1):
        j = rand_int(0, i)
        lst[i], lst[j] = lst[j], lst[i]

# ----------------------------------------------------------------------------
# 2. CARD / DECK LOGIC
# ----------------------------------------------------------------------------

# cards are tuples of (rank, suit), where:
#  rank is an integer 2..14 (2..10, 11=J, 12=Q, 13=K, 14=A)
#  suit is an integer 0..3 (0=Hearts, 1=Diamonds, 2=Clubs, 3=Spades)
# easier to sort and evaluate.

def make_deck():
    """ Return a list of 52 unique cards (rank, suit). """
    deck = []
    for rank in range(2, 15):      # 2..14
        for suit in range(4):     # 0..3
            deck.append((rank, suit))
    return deck

def card_str(card):
    """
    Return a string representation, e.g. "AH" for Ace of Hearts, "TD" for 10 of Diamonds, etc.
    Suits: 0=H, 1=D, 2=C, 3=S
    Ranks: 2..9, T=10, J=11, Q=12, K=13, A=14
    Just for display.
    """
    rank, suit = card
    rank_map = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}
    if rank <= 9:
        r = str(rank)
    elif rank == 10:
        r = 'T'
    else:
        r = rank_map[rank]

    suit_map = {0: 'H', 1: 'D', 2: 'C', 3: 'S'}
    s = suit_map[suit]
    return r + s

def remove_cards_from_deck(deck, cards_to_remove):
    """ Remove each card in cards_to_remove from deck if present. """
    # building a new list that excludes them
    # or remove in place. Let's do in place for clarity.
    new_deck = []
    set_remove = set(cards_to_remove)  # convert to set for quick membership
    for c in deck:
        if c not in set_remove:
            new_deck.append(c)
    return new_deck

# ----------------------------------------------------------------------------
# 3. POKER HAND EVALUATION (7-card -> best 5 -> rank)
# ----------------------------------------------------------------------------

def rank_7cards(cards7):
    """
    Given 7 cards (as (rank, suit)), return the best 5-card hand rank.
    We'll do it by enumerating all 5-card subsets, ranking them, and
    taking the maximum. We'll define a function rank_5cards(...) 
    that returns a comparable tuple.

    We have to write our own combination logic (no itertools).
    """
    best = (0, )  # track best rank tuple
    n = len(cards7)
    # We want all 5-combinations of these 7 cards: C(7,5)=21 combos
    # We'll just do a triple-nested approach or something systematic.
    # A straightforward approach is a 7 nested loops, but we can do simpler.
    # Let's pick indices i<j<k<l<m for i in [0..n-5], etc.
    for i in range(0, n-4):
        for j in range(i+1, n-3):
            for k in range(j+1, n-2):
                for l in range(k+1, n-1):
                    for m in range(l+1, n):
                        combo5 = [cards7[i], cards7[j], cards7[k], cards7[l], cards7[m]]
                        r5 = rank_5cards(combo5)
                        if r5 > best:
                            best = r5
    return best

def rank_5cards(cards5):
    """
    Return a tuple that represents the rank of these 5 cards 
    in standard poker. We'll use the common categories:
      9 = Straight Flush
      8 = Four of a Kind
      7 = Full House
      6 = Flush
      5 = Straight
      4 = Three of a Kind
      3 = Two Pair
      2 = One Pair
      1 = High Card
    We'll also build tie-breakers into the tuple. Larger tuple = better.

    For example, a typical rank tuple might look like:
       (category, primary_val, kicker1, kicker2, kicker3, kicker4, ...)
    We'll keep them in descending order for comparison.

    Steps to identify the hand:
      1) Sort the cards by rank descending
      2) Check for flush
      3) Check for straight
      4) Check duplicates (pairs, trips, quads)
      5) Construct the final rank tuple

    We do everything manually (no library).
    """
    # Sort by rank descending
    sorted_cards = sorted(cards5, key=lambda c: c[0], reverse=True)
    ranks = [c[0] for c in sorted_cards]
    suits = [c[1] for c in sorted_cards]

    # Count occurrences of each rank
    rank_counts = {}
    for r in ranks:
        if r not in rank_counts:
            rank_counts[r] = 0
        rank_counts[r] += 1

    # Check for flush (all 5 suits the same)
    is_flush = (suits.count(suits[0]) == 5)

    # Check for straight:
    # A normal straight is 5 consecutive ranks (like 8,7,6,5,4).
    # Also handle the special A-2-3-4-5 case. (Ace can be "low".)
    is_straight = False
    top_straight_rank = 0

    # A simple way: take the distinct ranks in descending order.
    distinct_ranks_desc = []
    for r in ranks:
        if r not in distinct_ranks_desc:
            distinct_ranks_desc.append(r)
    # e.g. for Q,Q,9,8,7 => distinct_ranks_desc = [Q,9,8,7]

    # normal check
    if len(distinct_ranks_desc) >= 5:
        # Walk through distinct ranks to see if we have 5 consecutive
        for start_index in range(len(distinct_ranks_desc) - 4):
            seq = distinct_ranks_desc[start_index:start_index+5]
            # Check if they're consecutive
            if (seq[0] - seq[4] == 4):  # e.g. 9,8,7,6,5 => 9-5=4
                is_straight = True
                top_straight_rank = seq[0]
                break

        # Special case: A,5,4,3,2
        # That would appear as ranks like [A, 5,4,3,2].
        # Ace=14, so 14,5,4,3,2 => we check if 14 in distinct and also 2,3,4,5
        # If yes, then top_straight_rank = 5 (the top for the A-2-3-4-5 wheel).
        if not is_straight:
            if 14 in distinct_ranks_desc and 5 in distinct_ranks_desc and \
               4 in distinct_ranks_desc and 3 in distinct_ranks_desc and 2 in distinct_ranks_desc:
                is_straight = True
                top_straight_rank = 5  # "5 high" straight

    # Check for Straight Flush
    if is_flush and is_straight:
        # Category 9
        return (9, top_straight_rank)

    # Count how many of each rank we have: we already have rank_counts
    # Let's separate them by frequency
    # Example for full house with Q,Q,Q,7,7 => rank_counts = {Q:3, 7:2}
    # We'll build a list of (count, rank), sorted descending by count, then rank
    count_rank_pairs = []
    for r, cnt in rank_counts.items():
        count_rank_pairs.append((cnt, r))
    # Sort by count descending, then rank descending
    # e.g. for Q=3, 7=2 => we get (3,Q), (2,7)
    # for four-of-a-kind => maybe (4,10), (1,3)
    count_rank_pairs.sort(key=lambda x: (x[0], x[1]), reverse=True)

    # Now we can handle Four of a Kind, Full House, Trips, Two Pair, One Pair
    # Check the structure of count_rank_pairs.
    # Example structures:
    #  Four of a Kind: (4, R) + (1, Kicker)
    #  Full House: (3, R1) + (2, R2)
    #  Trips: (3, R) + (1, K1) + (1, K2)
    #  Two Pair: (2, R1) + (2, R2) + (1, Kicker)
    #  One Pair: (2, R) + (1, K1) + (1, K2) + (1, K3)
    #  High Card: everything is (1, ...)

    # Let's store them in a simpler form:
    # e.g. for (3, Q), (2, 7) => that means 3 Qs, 2 7s
    # We'll figure out category from the pattern of counts
    # Then build a tiebreak list from highest to lowest rank within each group
    # For example, a Full House with QQQ77 => category=7, tiebreak=(Q,7)

    # We'll parse out the pattern of counts
    # Something like [4,1], [3,2], [3,1,1], [2,2,1], [2,1,1,1], [1,1,1,1,1]
    counts_only = [p[0] for p in count_rank_pairs]

    if counts_only[0] == 4:
        # Four of a Kind
        # (8, rank_of_4, kicker)
        four_rank = count_rank_pairs[0][1]
        kicker = count_rank_pairs[1][1]
        return (8, four_rank, kicker)

    if counts_only[0] == 3:
        # Could be Full House or Three of a Kind
        if len(counts_only) > 1 and counts_only[1] == 2:
            # Full House
            trip_rank = count_rank_pairs[0][1]
            pair_rank = count_rank_pairs[1][1]
            return (7, trip_rank, pair_rank)
        else:
            # Just trips
            trip_rank = count_rank_pairs[0][1]
            # Then the kickers come from the next ones in descending order
            # e.g. (3,9), (1,5), (1,3)
            # Actually that wouldn't happen for the same rank, so let's just gather them
            kickers = []
            for i in range(1, len(count_rank_pairs)):
                cnt, rnk = count_rank_pairs[i]
                # if count=2, that means it's 2 of same rank, that rank is better kicker
                # but let's just store them. We'll have cnt occurrences, so we might have up to 2 or 3 single ranks
                for _ in range(cnt):
                    kickers.append(rnk)
            # Sort descending
            kickers.sort(reverse=True)
            return (4, trip_rank) + tuple(kickers)

    if counts_only[0] == 2:
        # Could be Two Pair or One Pair
        if len(counts_only) > 1 and counts_only[1] == 2:
            # Two pair
            pair1_rank = count_rank_pairs[0][1]
            pair2_rank = count_rank_pairs[1][1]
            # next is kicker
            kicker = count_rank_pairs[2][1]
            # category=3
            # Tiebreak: pair1_rank, pair2_rank, kicker
            # Make sure pair1_rank >= pair2_rank
            if pair1_rank < pair2_rank:
                pair1_rank, pair2_rank = pair2_rank, pair1_rank
            return (3, pair1_rank, pair2_rank, kicker)
        else:
            # One pair
            pair_rank = count_rank_pairs[0][1]
            # gather the 3 kickers
            kickers = []
            for i in range(1, len(count_rank_pairs)):
                (cnt, rnk) = count_rank_pairs[i]
                for _ in range(cnt):
                    kickers.append(rnk)
            kickers.sort(reverse=True)
            return (2, pair_rank, kickers[0], kickers[1], kickers[2])

    # If we get here, no pairs/trips/quads => either straight, flush, or high card
    if is_flush:
        # category=6 (Flush)
        # tiebreak => ranks in descending order
        # We can just use the sorted ranks as is
        return (6, ranks[0], ranks[1], ranks[2], ranks[3], ranks[4])

    if is_straight:
        # category=5 (Straight)
        return (5, top_straight_rank)

    # else just High Card
    return (1, ranks[0], ranks[1], ranks[2], ranks[3], ranks[4])

# ----------------------------------------------------------------------------
# 4. MONTE CARLO WIN PROBABILITY
# ----------------------------------------------------------------------------

def simulate_win_probability(player_cards, known_community, num_opponents, deck, sims=5000):
    """
    Estimate the probability that the player's final 7-card hand is best at showdown
    among 'num_opponents', given that we already know:
     - player's 2 hole cards
     - 'known_community' (0..4 known community cards so far)
     - a deck that still has 52 - (2 + known_community + opponents*2??)...

    We'll do a Monte Carlo approach:
      - For each simulation:
        1) Clone the deck (minus the known cards).
        2) Randomly deal the remaining community cards (to make total 5).
        3) Randomly deal each opponent 2 hole cards.
        4) Evaluate all hands (7 cards each) and see if we have the highest hand.
      - Count how many times we "win or tie" / total sims.

    We do this from scratch with no library.
    """
    # First, gather all known cards in use:
    # player's 2 + known_community
    # We do NOT remove opponents' hole cards from the deck, since we don't know them.
    # We'll remove these known from the deck, then for each simulation randomly pick
    # the rest of the community cards and opponents' hole cards from what's left.
    used_cards = []
    for c in player_cards:
        used_cards.append(c)
    for c in known_community:
        used_cards.append(c)

    # Build a reduced deck that excludes used_cards
    base_deck = []
    for c in deck:
        if c not in used_cards:
            base_deck.append(c)

    wins = 0
    ties = 0
    total = 0

    # We'll do 'sims' simulations
    for _ in range(sims):
        # We copy base_deck -> sim_deck for each simulation, then "shuffle" and pick from top
        sim_deck = base_deck[:]
        shuffle_in_place(sim_deck)

        # Complete the community to 5 cards
        community_needed = 5 - len(known_community)
        community_rest = sim_deck[:community_needed]
        sim_deck = sim_deck[community_needed:]
        full_community = known_community + community_rest

        # Deal each opponent 2 hole cards
        opp_holes = []
        for _opp in range(num_opponents):
            hole = sim_deck[:2]
            sim_deck = sim_deck[2:]
            opp_holes.append(hole)

        # Evaluate player's best 5 out of 7
        player_7 = player_cards + full_community
        player_rank = rank_7cards(player_7)

        # Evaluate each opponent
        best_count = 0
        same_count = 0
        for oh in opp_holes:
            opp_7 = oh + full_community
            opp_rank = rank_7cards(opp_7)
            if opp_rank > player_rank:
                best_count += 1
            elif opp_rank == player_rank:
                same_count += 1

        if best_count == 0:
            # That means no one beat the player
            if same_count == 0:
                # we outright win
                wins += 1
            else:
                # we tie with 'same_count' people
                ties += 1
        total += 1

    # Probability that we are best or tied for best = (wins + ties) / total
    # If you only want strictly best, you can just do wins / total. But let's do best-or-tie:
    return float(wins + ties) / float(total)

# ----------------------------------------------------------------------------
# 5. MAIN GAME FLOW
# ----------------------------------------------------------------------------

def poker_demo():
    # Make a deck, shuffle it
    deck = make_deck()
    shuffle_in_place(deck)

    print("Welcome to No-Library Texas Hold'em!")
    # Ask user for number of opponents
    while True:
        num_opps_str = input("How many opponents do you want to face? (1-5 suggested) ")
        if num_opps_str.isdigit():
            num_opps = int(num_opps_str)
            if num_opps >= 1 and num_opps <= 9:
                break
        print("Invalid. Enter a number 1..9.")

    # Deal your 2 hole cards
    player_cards = [deck.pop(), deck.pop()]
    # For each opponent, deal 2 hole cards (unknown to you, but we store them if we want a final showdown)
    opponents = []
    for _ in range(num_opps):
        opp2 = [deck.pop(), deck.pop()]
        opponents.append(opp2)

    # We'll reveal the community street by street
    # Pre-Flop: known_community = []
    known_community = []

    # Pre-Flop Probability
    preflop_prob = simulate_win_probability(player_cards, known_community, num_opps, deck, sims=3000)

    print("\nYour hole cards:")
    print(card_str(player_cards[0]), card_str(player_cards[1]))
    print("Estimated probability of winning at showdown (pre-flop): {:.1f}%".format(100.0*preflop_prob))

    action = input("Pre-Flop Action: [C]all or [F]old? ")
    if action.lower() == 'f':
        print("You folded. Game ends.")
        return

    # Flop
    flop = [deck.pop(), deck.pop(), deck.pop()]
    known_community = flop[:]
    flop_prob = simulate_win_probability(player_cards, known_community, num_opps, deck, sims=3000)
    print("\n--- FLOP ---")
    print("Community cards:", " ".join(card_str(c) for c in known_community))
    print("Win probability now: {:.1f}%".format(flop_prob*100.0))
    action = input("Flop Action: [C]all or [F]old? ")
    if action.lower() == 'f':
        print("You folded. Game ends.")
        return

    # Turn
    turn = deck.pop()
    known_community.append(turn)
    turn_prob = simulate_win_probability(player_cards, known_community, num_opps, deck, sims=3000)
    print("\n--- TURN ---")
    print("Community cards:", " ".join(card_str(c) for c in known_community))
    print("Win probability now: {:.1f}%".format(turn_prob*100.0))
    action = input("Turn Action: [C]all or [F]old? ")
    if action.lower() == 'f':
        print("You folded. Game ends.")
        return

    # River
    river = deck.pop()
    known_community.append(river)
    river_prob = simulate_win_probability(player_cards, known_community, num_opps, deck, sims=3000)
    print("\n--- RIVER ---")
    print("Community cards:", " ".join(card_str(c) for c in known_community))
    print("Win probability now: {:.1f}%".format(river_prob*100.0))
    action = input("River Action: [C]all or [F]old? ")
    if action.lower() == 'f':
        print("You folded. Game ends.")
        return

    # Final Showdown (for demonstration):
    print("\n--- SHOWDOWN ---")
    print("Your final 7 cards:", " ".join(card_str(c) for c in (player_cards + known_community)))
    player_rank = rank_7cards(player_cards + known_community)

    # Evaluate each opponent
    winners = 0
    ties = 0
    for i, opp_hc in enumerate(opponents):
        opp_final = opp_hc + known_community
        opp_rank = rank_7cards(opp_final)
        # We'll reveal them for the user
        print("Opponent #{} hole cards: {} {}".format(i+1, card_str(opp_hc[0]), card_str(opp_hc[1])))
        if opp_rank > player_rank:
            winners += 1
        elif opp_rank == player_rank:
            ties += 1

    if winners == 0:
        if ties == 0:
            print("You Win outright!")
        else:
            print("You Tied with {} others!".format(ties))
    else:
        print("You Lost. {} opponents have better hands.".format(winners))

# ----------------------------------------------------------------------------
# RUN
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    poker_demo()
