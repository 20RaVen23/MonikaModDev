# Module holding jokes that you can tell to monika
# as well as jokes monika tells to you
#
# we are now using an event db. (not the big one, just a special two for us)

# list of tags that we have blocked
default persistent.jokes_tags_blocked = []

# how many jokes available today
default persistent.jokes_available = masjokes.JOKE_DAILY_MAX

# how many dark jokes have we told
# default persistent.jokes_dark_told = 0

# the JOKES DB.
# similar to events except we doing things a bit differently.
# MAIN DIFFS:
#   eventlabel - still 
#   category - this system will be used to differentiate between joke types.
#       and allow us to apply filtering blocks
#   unlocked - we dont actually use this to signifiy if a joke is unlocked.
#       instead, we use the category as a filtering rule. 
#       NOTE: if we end up having jokes that rely on a previous joke, then
#           we apply this property
#   prompt - in p2m jokes, this is a joke setup line. In m2p jokes, its like
#       a descriptor.
#   conditional - these are NOT evaluated. NOTE: if we endup having to use
#       unlocked, then we will consider doing this as well.
#   
# NOTE: we are using the new Event system where data is stored in persistent
# but Events are stored in a separate dict that points to said persistent
default persistent.jokes_database = {}

# pre stuff
init -1 python:

    def randomlyRemoveFromListPool(pool, n):
        #
        # randomly returns n number of items from teh given pool. The pool 
        # must be a list. If there are less than n items in the pool, then the 
        # pool is returned. Returned items are removed from teh pool.
        #
        # IN:
        #   pool - list that we want to retrieve from
        #   n - number of items to remove off the pool
        #
        # RETURNS:
        #   n number of items, randomly selected, or len(pool) number of items
        #   if n < len(pool)
        
        if len(pool) < n:
            n = len(pool)

        # remove n number of items
        removed = list()
        for i in range(0,n):
            item = renpy.random.choice(pool)
            removed.append(item)
            pool.remove(item)
        return removed

init -1 python in masjokes:
    # only 3 choices at a time
    OPTION_MAX = 3

    # how many jokes can we say? 
    # per day?
    JOKE_DAILY_MAX = 3

    # JOKE types
    TYPE_DARK = "dark"
    TYPE_DAD = "dad"
    TYPE_PUN = "pun"
    TYPE_CS = "cs" # programmer related humor

    # dict storage of Events
    jokes_m2p_db = dict()
    jokes_p2m_db = dict()

    # list storage of everything
    all_m2p_jokes = list()
    all_p2m_jokes = list()
    use_m2p_jokes = list()
    use_p2m_jokes = list()
    day_m2p_jokes = list()
    day_p2m_jokes = list()

    # are jokes unlocked
    jokes_unlocked = False


init 5 python in masjokes:

    def filterJoke(joke, seen=False):
        #
        # Filters the given joke accoridng to persistent rule
        #
        # IN:
        #   joke - Event object joke to filter
        #   seen - True if we want to include seen jokes, false otherwise
        #
        # RETURNS:
        #   True if the joke passes the filter, false otherwise
        #
        # ASSUMES:
        #   persistent.jokes_tags_blocked

        # sanity check
        if not joke:
            return False

        # no seens allowed (if seen is False)
        if not seen and renpy.seen_label(joke.eventlabel):
            return False

        # no category is okay
        if not joke.category:
            return True

        # let the filtering begin
        for tag in renpy.store.persistent.jokes_tags_blocked:
            if tag in joke.category:
                return False

        # pass filtering rules
        return True

    def buildFilteredJokesList(jokedb, seen=False):
        #
        # builds a list of filtered jokes given the jokedb
        #
        # IN:
        #   jokedb - the dict of Event jokes to filter
        #   seen - True if we want to include seen jokes, false otherwise
        #
        # RETURNS:
        #   list of filtered jokes
        return [ev for k,ev in jokedb.iteritems() if filterJoke(ev, seen)]

    def buildUnseenJokesList(joke_list):
        #
        # Builds list of unseen jokes given the joke list
        # 
        # IN:
        #   joke_list - list of Event jokes to filter
        #
        # RETURNS:
        #   list of unseen jokes
        return [ev for ev in joke_list if not renpy.seen_label(ev.eventlabel)]


# post stuff
init 10 python:
    import copy
    import store.masjokes as masjokes

    # jokes are unlocked after seeing this label
    masjokes.jokes_unlocked = renpy.seen_label("monika_urgent")

    # all lists are all jokes minus filters
    masjokes.all_m2p_jokes = masjokes.buildFilteredJokesList(
        store.masjokes.jokes_m2p_db,
        seen=True
    )
    masjokes.all_p2m_jokes = masjokes.buildFilteredJokesList(
        store.masjokes.jokes_p2m_db,
        seen=True
    )

    # use lists are jokes that we havent seen.
    masjokes.use_m2p_jokes = masjokes.buildUnseenJokesList(
        masjokes.all_m2p_jokes
    )
    masjokes.use_p2m_jokes = masjokes.buildUnseenJokesList(
        masjokes.all_p2m_jokes
    )

    # NOTE: many of these things are going to be moved into the jokes
    # label instead. 
    # empty lists mean we need to reset
#    if len(masjokes.use_m2p_jokes) == 0:
#        masjokes.use_m2p_jokes = copy.copy(masjokes.all_m2p_jokes)
#    if len(masjokes.use_p2m_jokes) == 0:
#        masjokes.use_p2m_jokes = copy.copy(masjokes.all_p2m_jokes)

    # fill up the daily jokes list
#    masjokes.day_m2p_jokes = randomlyRemoveFromListPool(
#        masjokes.use_m2p_jokes,
#        masjokes.OPTION_MAX
#    )
#    masjokes.day_p2m_jokes = randomlyRemoveFromListPool(
#        masjokes.use_p2m_jokes,
#        masjokes.OPTION_MAX
#    )

    # resets should happen in the jokes topic

#################### JOKE LAUNCHER ############################################

# START LABEL
label joke_tell_joke:
    
    # you can only exchange a certain number of jokes per day
    if persistent.jokes_available > 0:
        $ import store.masjokes as masjokes
        $ import copy
        m "Hey [player], I think telling each other some good jokes could bring us closer together, you know?"
        m "I know quite a few jokes, but I was wondering if maybe you knew any."
        menu:
            m "Do you know any good jokes?"
            "{b}Yes{/b}" if len(masjokes.use_p2m_jokes) > 0:
                # we have new jokes to tell
                call joke_tell_monika

            "Yes" if len(masjokes.use_p2m_jokes) == 0:
                # we only have old jokes to share
                call joke_tell_monika
                m "TODO: dialogue about repeating jokes?"

            "{b}No{/b}" if len(masjokes.use_m2p_jokes) > 0:
                # monika has new jokes to tell
                m "Alright, I'll tell you a joke"
                jump joke_tell_player

            "No" if len(masjokes.use_m2p_jokes) == 0:
                # no new monika jokes
                # TODO: dialogue for no new jokes
                m "TODO: dialogue about not having any new jokes"
                menu:
                    m "Exchange old jokes?"
                    "Yes":
                        jump joke_tell_player_old
                    "No":
                        m "TODO: okay player I write more jokes soon"
    else:
        # TODO: better dialogue for no more available jokes
        m "No more jokes today I hate you"

label joke_tell_jokeend:
    # NOTE: this is called when we are done exchanging a joke.
    return

label joke_tell_monika:
    python:
        # check to ensure we arent dry
        if len(masjokes.day_p2m_jokes) == 0:

            # check if unseen isnt dry
            if len(masjokes.use_p2m_jokes) == 0:
                masjokes.use_p2m_jokes = copy.copy(masjokes.all_p2m_jokes)

            # pull randomly
            masjokes.day_p2m_jokes = randomlyRemoveFromListPool(
                masjokes.use_p2m_jokes,
                masjokes.OPTION_MAX
            )

    m "Ah, do you mind letting me hear some?"

    python:
        # using display menu requires a processing
        p2m_jokeslist = list()
        for joke in masjokes.day_p2m_jokes:
            p2m_jokeslist.append((joke.prompt,joke))

        # now call the menu
        sel_joke = renpy.display_menu(p2m_jokeslist)

    # and the resulting label
    call expression sel_joke.eventlabel from _p2m_joke_subexp
    $ masjokes.day_p2m_jokes.remove(sel_joke)
    $ persistent.jokes_available -= 1

    # dark joke code
    if masjokes.TYPE_DARK in sel_joke.category:
        $ persistent.dark_jokes_told += 1
    return

label joke_tell_player_old:
    python:
        # check to ensure we arent dry
#        if len(masjokes.day_m2p_jokes) == 0:

        # check if unseen isnt dry
#        if len(masjokes.use_m2p_jokes) == 0:
        masjokes.use_m2p_jokes = copy.copy(masjokes.all_m2p_jokes)

        # pull randomly
#        masjokes.day_m2p_jokes = randomlyRemoveFromListPool(
#            masjokes.use_m2p_jokes,
#            masjokes.OPTION_MAX
#        )

label joke_tell_player:
    # now pick one monika
    $ sel_joke = renpy.random.choice(masjokes.use_m2p_jokes)
    call expression sel_joke.eventlabel from _m2p_joke_subexp
    $ masjokes.use_m2p_jokes.remove(sel_joke)
    $ persistent.jokes_available -= 1
    
    jump joke_tell_jokeend

#=============================================================================#
# PLAYER 2 MONIKA JOKES
#=============================================================================#

init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_moonrestaurant",
            prompt="Did you hear about the restaurant on the moon?",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )

    
label joke_moonrestaurant:
    menu:
        "It has great service but there's no atmosphere.":
            m 3l "Ahaha, maybe a better atmosphere would make this restaurant {i}out of this world{/i}!"
            m 2a"Some candles, plants and oxygen would make the place great."
            m "Hope you didn't {i}planet{/i}!"
            m 1j "Gosh, I should stop for now!"
            m "I'll tell you any bad jokes you want other time ehehe~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_scarecrowaward",
            prompt="Why did the scarecrow win an award?",
            category=[store.masjokes.TYPE_DAD, store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )

label joke_scarecrowaward:
    menu:
        "He was outstanding in his field.":
            m 4f "Ah, you can't be serious."
            m 2b "You've to consider that farming jokes are quite corny ehehe~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_fencegraveyard",
            prompt=("A curious child asks his dad 'Why do they build a fence" +
                " around a graveyard?'"
            ),
            category=[store.masjokes.TYPE_DAD, store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )

label joke_fencegraveyard:
    menu:
        "The dad quickly replies with 'Because people are dying to get in there!'":
            m 3b "Some people do get in like the writer who was sentenced to death!"
            m "Yet just skeletons can't get in since they have nobody to enter with."
            m 2f "It's a bit discriminative if you ask me."
            m 2j "We could call it a grave mistake."
            m 2k "Ahaha, I'm sorry [player], I didn't mean to bore you to death with those puns."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_knocknobel",
            prompt="Did you hear about the guy who invented knock knock jokes?",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )

label joke_knocknobel:
    menu:
        "Turns out he won the nobel prize.":
            m 3e "Well, I hope he could handle the pressure."
            m 2b "It's after all an unbellievable situation."
            m "I am glad he wasn't doormant in the middle of the awards."
            m 1l "Hope you do love my bad puns [player]! Ehehe~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_mushroomfungai",
            prompt="A mushroom walks into a bar.",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_mushroomfungai:
    menu:
        "The bartender says, 'Hey, get out of here! We don’t serve mushrooms here'":
            menu:
                "The mushroom says, 'Why not? I’m a fungi!'":
                    m 2b "Poor mushroom, maybe he wasn't allowed in cause there wasn't {i}mushroom{/i}!"
                    m 3p "I don't know that many mushroom jokes."
                    m 3n "Maybe I should just try to make other puns just for you ehehe~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_hitired",
            prompt="How many apples grow on a tree?",
            category=[store.masjokes.TYPE_DAD]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )

label joke_hitired:
    m 1q "Ah, [player] please give me a second"
    m "I don't know why but I haven't been feeling that good today."
    m 2p "I'll try to guess your joke in a second."
    menu:
        m "Yet for now I'm tired, that's all."
        "Hi tired, I'm [player]!":
            m 4g "..."
            m "Did you just seriously tell me that?"
            m 2d "I really can't believe it."
            m "You just played on me the ultimate dad joke."
            m 2k"Gosh, [player]!"
            m 3e "You should know that your joke qualifies as a dad joke completely."
            m "There's only one reason it does!"
            m 3j "Your joke became apparent."
            m "..."
            m 1l "Ahaha, that should make up for your joke!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_cantopener",
            prompt="What do you call a broken can opener?",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )

label joke_cantopener:
    menu:
        "A can't opener!":
            m 1g "I... I didn't think it was possible to think up such a terrible joke."
            m 3c "[player], you do understand how the concept of humor works, right?"
            m 3l "You should get a bro{i}kan{/i} opener! Ehehe~" 
            m "That's the proper way to do it."
            m 3b "If your joke doesn't stand out then it might get lost in a {i}can{/i}yon of bad jokes."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_camouflagetraining",
            prompt=("At evening roll call, the sergeant-major headed right " +
                "towards a young soldier."
            )
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_camouflagetraining:
    menu:
        "The sergeant-major growled at the young soldier, 'I didn’t see you at camouflage training this morning!'":
            menu:
                "The soldier replied: 'Thank you very much, sir.'":
                    m 1l "Ahaha, quite funny [player]."
                    m 3e "Although I believe there're better kinds of camouflage."
                    m "Like for example, how does a cow become invisible?"
                    m 1j "Through camooflage!"
                    m 2p "Gosh, I just can't find a better pun for camouflage."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_muffledexhausted",
            prompt="Last night I had a dream I was a muffler.",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_muffledexhausted:
    menu:
        "I woke up exhausted.":
            m "Ah in that case you should try to dream of being a bicycle!"
            m "Although you might sleep badly since you would be two tired."
            m "In that case {i}wheel{/i} see a better solution."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_threewishes",
            prompt=("Three guys, who are stranded on an island, find a magic" +
                " lantern which contains a genie, who will grant three " +
                "wishes."
            ),
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )

label joke_threewishes:
    menu:
        "The first guy wishes for a way off the island, the second guy wishes for the same as the first guy...":
            menu:
                "Finally, the third guy says: 'I'm lonely. I wish my friends were back here.'":
                    m 4p "The first and second guys must be feeling sad."
                    m 3b"I hope the third guy was shore of his sailection on that wish."
                    m "At least we could call it a seantimental reunion!"
                    m "From now on it might seem like seaparation is impossible."
                    m 2l "After all, they'll have to sea each other for a long time."
    return

    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_sodapressing",
            prompt="Why did the can-crusher quit his job?",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_sodapressing:
    menu:
        "Because it was soda-pressing!":
            m 2k "Ahaha, I see."
            m 1a "That joke is pretty bad, I just think you should can it!"
            m 3j "{i}So daring{/i} to tell such a bad pun to me! Ehehe~"
            return
            

init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_haircut",
            prompt="Did you ever get a haircut?",
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_haircut:
    m 3e "Ah, you're wrong there!"
    m 4j "I didn't get a haircut, I got several cut!  Ehehe~"
    m "Sorry, I simply saw the chance to answer back."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_pooldeepends",
            prompt="Are pools safe for diving?",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_pooldeepends:
    menu:
        "It deep ends!":
            m 4j "Honestly [player], I think you could pool off something better!"
            m 4l"Put some more effort into it next time! Ehehe~"
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_atomtrustissues",
            prompt="You shouldn't trust atoms!"
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_atomtrustissues:
    menu:
        "They make up everything.":
            m 2j "You should just get {i}a tome{/i}of jokes."
            m "It might be useful but then again, it's made out of atoms!"
            m 2k "Ahaha, I'm made out of atoms too so are you."
            m 4p "Gosh, you have created a gigantic contradiction!."
            return

init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_hamdiscrimination",
            prompt="A ham sandwich walks into a bar."
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_hamdiscrimination:
    menu:
        "The bartender says ‘Sorry we don’t serve food here!’.":
            m 1b "That's a really tough way to {i}hammer{/i} his point."
            m 3b "I personally believe this discrimination was hamful."
            m 4j "Would the bartender serve food if the ham was instead a {i}hamster{/i}?"
            return
            

init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_mineistheanswer",
            prompt="A cop stops a miner for speeding on the highway."
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_mineistheanswer:
    menu:
        "The cop asks the miner; 'Whose car is this? Where are you headed? What do you do?'":
            menu:
                "The miner replies; 'Mine.'":
                    m 2b "It seems like you've hit rock bottom with this joke."
                    m 3a "I just have a cobble of rock puns."
                    m  "Not every pun can be a gem."
                    m 4k "Some just fall under the pressure."
                    m "You've to avoid taking these puns for granite."
                    return
                
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_beaverdamn",
            prompt="I just watched a show about beavers.",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_beaverdamn:
    menu:
        "It was the best damn thing ever.":
            m 4j "You wood need some better beaver puns for next time!"
            m 4l "Beavery careful with the puns you say! Ehehe~"
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_themuggedcoffee",
            prompt="Why did the coffee file a police report?",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )

label joke_themuggedcoffee:
    menu:
        "It was mugged!":
            m 3b "I see, I wonder if the coffee procaffeinated filing that report."
            m "Getting mugged must be a bitter thing to happen to you."
            m 2j "I hope the coffee has bean okay after all this!"
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_tearablepaper",
            prompt="Wanna hear a joke about paper?",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )

label joke_tearablepaper:
    menu:
        "Nevermind, it's just tearable!":
            m 4a "Your joke's quite flimsy."
            m 1b "If it was a bit better then we could make it pay-per view!"
            m 1l "Although for now all I can say is that it's far away from being a paperfect joke."
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_groundbreakingshovel",
            prompt="I think quite highly of the shovel.",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_groundbreakingshovel:
    menu:
        "It was after all, a ground breaking invention.":
            m 1a "You really shoveled that joke out."
            m 1k "It's a hole other joke compared to what one might expect. Ehehe~"
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_igloosit",
            prompt="How does a penguin build it's house?",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
            
label joke_igloosit:
    menu:
        "Igloos it together!":
            m 2e "I think that house would fall down under harsh weather, you snow?"
            m "I hope that penguin doesn't get excited over his new house and ends up giving the cold shoulder to other penguins!"
            m 3b "If somebody's in trouble then he should offer his alp!"
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_irrelephant",
            prompt="What do you call an elephant that doesn't matter?",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_irrelephant:
    menu:
        "An irrelephant!":
            m 4b "I assume coming up with that one was a tough tusk."
            m 1k "Making bad jokes like this is quite a big deal! Ehehe~"
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_nutsdiet",
            prompt="I thought about going on an all-almond diet.",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_nutsdiet:
    menu:
        "But that's just nuts!":
            m 2k "Ahaha, you really went nuts with that joke."
            m 4j "If we're doing food jokes then you should watch out."
            m "There's a cereal killer around."
            m 1k "The police says 'Lettuce know if you see him.'"
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_kidnappingatschool",
            prompt="Did you hear about the kidnapping at one school?",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_kidnappingatschool:
    menu:
        "It's fine, he woke up.":
            m 3k "Ahaha, impressive."
            m 2p "Hope he could get a bed to nap on."
            m 1b "Otherwise he wouldn't get a beddy good sleep!"
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_resistingarest",
            prompt="If a child refuses to sleep during night time.",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_resistingarest:
    menu:
        "Are they guilty of resisting a rest?":
            m 2b "I doubt the police could catch him in that case."
            m 2l "The child always sleeps away just when they're about to get him."
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_stepahead",
            prompt="I leave my right shoe inside my car.",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_stepahead:
    menu:
        "You could say I'm a step ahead!":
            m 4a "I believe you went a step too far with this joke."
            m "You should take baby steps first."
            m 1j "After all, a joke is not a cake walk."
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_leastspokenlanguage",
            prompt="What's the least spoken language in the world?"
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_leastspokenlanguage:
    menu:
        "Sign language.":
            m 1b "I should've seen that one coming."
            m 4k "The signs were pretty clear! Ehehe~"
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_octover",
            prompt="What do you say when november starts?",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_octover:
    menu:
        "Octover!":
            m 2j "I hope you {i}may{/i} come up with something better."
            m 2k "{i}March{/i} onwards until you can come up with something else! Ehehe~"
            return
                    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_leekinginformation",
            prompt="Why did the vegetable go to jail?",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
        
label joke_leekinginformation:
    menu:
        "Because he was leeking information.":
            m 3n "That joke was as salad as rock!"
            m 2j "I herb that one a while ago. Ehehe~"
            return

init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_timidpebble",
            prompt="What did the timid pebble wish for?"
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_timidpebble:
    menu:
        "It wished it could be a little bolder.":
            m 1a "That jokes was crystal clear."
            m 4k "I liked how concrete it was! Ehehe~"
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_chickenslide",
            prompt="Why did the chicken cross the playground?"
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_chickenslide:
    menu:
        "To get to the other slide.":
            m 4b "I see the chicken decided to swing to that side!"
            m 1l "Ahaha, sorry [player], I just can't think of any other pun."
            return

init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_nicejester",
            prompt="Yesterday a clown held the door open for me.",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_nicejester:
    menu:
        "I thought it was a nice jester!":
            m 2a"It could have been a nice jester yet it must have felt funny."
            m 4b "After all, clowns have a funny bone."
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_caketiers",
            prompt="It was an emotional wedding.",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_caketiers:
    menu:
        "Even the cake was in tiers!":
            m 3b "Bake in my day cakes were smaller!"
            m "I suppose the cake having tiers was half-baked."
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_housewearadress",
            prompt="What does a house wear?",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_housewearadress:
    menu:
        "A dress":
            m 1b "I roofly saw that one coming."
            m 1l "If the house had more stuff, that would be grate."
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_aimisgettingbetter",
            prompt="My ex-wife still misses me.",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_aimisgettingbetter:
    menu:
        "But her aim's steadily improving.":
            m 2n "I can only say one thing about your joke."
            m 4k "It's a {i}daimond{/i}!"
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_daywellspent",
            prompt="If you spent your day in a well.",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_daywellspent:
    menu:
        "Would it be a day well-spent?":
            m 1a "Oh well, you don't always win."
            m 4k "Sometimes you just can't see well! Ehehe~"
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_massconfusion",
            prompt="If America changed from pounds to kilograms.",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_massconfusion:
    menu:
        "It would be a mass confusion.":
            m 1a "If the metric system was changed too then it would be a feetiful situation."
            m 1b "Of course it would cause chaos too."
            m 3j "We shouldn't get into meters like these."
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_justchilling",
            prompt="What do snowmen do in their free time?",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_justchilling:
    menu:
        "Just chilling!":
            m 1b "At least that's a good joke for breaking the ice."
            m "At frost glance it seems a lot worse."
            m 4j "It can clearly sled somebody to the wrong conclusion!"
            return
            
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_trainderailer",
            prompt="A boss yelled at a driver the other day.",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
    
label joke_trainderailer:
    menu:
        "He said 'You've got to be the worst train driver. How many trains did you derail last year?'":
            menu:
                "The driver said 'I don't know, I'ts hard to keep track!'":
                    m 1a "That driver should train his driving skills."
                    m 1b "He must have a loco-motive for doing that!"
                    m 4k "I feel like his life's going onto the wrong track. Ehehe~"
                    return
                    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "joke_wealldig",
            prompt="I dig, you dig, she dig, he dig, we dig...",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_p2m_db
    )
            
label joke_wealldig:
    menu:
        "...the poem may not be beatiful, but it's certainly very deep.":
            m 1a "That poem's the hole truth!"
            m 1j "Your next joke better not deep me dissapointed."
            return
#=============================================================================#
# MONIKA 2 PLAYER JOKES
#=============================================================================#

init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_bakercollege",
            prompt="Baker College",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )

label m_joke_bakercollege:
    m 1a "What did the baker say when he had to go through college?"
    m 2b "Piece of cake!"
    m 3o "I wonder if Natsuki would have said the same thing."
    m 2l "Maybe she would loaf it! Ehehe~"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_gluehistory",
            prompt="Glue History",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )

label m_joke_gluehistory:
    m 2a"I’ve been reading a book on the history of glue."
    m 2b "I just can’t seem to put it down."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_knifetoknowyou",
            prompt="Nice to know you",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_knifetoknowyou:
    m 2a "What did the serial murderer tell their victim?"
    m 2b "It was knife knowing you."
    m 1p "Now that I think about it, this joke reminds me of Yuri."
    m 4b "I believe she would have laughed at that joke for a knifeti- I mean, a lifetime!"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_natsukishelf",
            prompt="My shelf",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )

label m_joke_natsukishelf:
    m 3a "I would have felt horrible if Natsuki had been hurt by those falling books."
    m 2l "I'd only have my shelf to blame."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_undercoverbook",
            prompt="Undercover",
            category=[store.masjokes.TYPE_PUN],
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )

label m_joke_undercoverbook:
    m 1a "Why did the book join the police?"
    m 2j "He wanted to go undercover."
    return

init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_authlete",
            prompt="Authors",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_authlete:
    m 1a "What do you call a writer who completes a whole book in one day?"
    m 4e "You call him an authlete!"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_stockholmbook",
            prompt="Stockholm Syndrome",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_stockholmbook:
    m 1a "I just read a textbook about Stockholm Syndrome."
    m 2j"The first couple chapters were awful but by the end I loved it."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_sinkholebook",
            prompt="Sinkholes",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_sinkholebook:
    m 1a "I had plans to begin reading a book about sinkholes."
    m 1b "Sadly my plans fell through."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_penciltobeornot",
            prompt="Pencils",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )

label m_joke_penciltobeornot:
    m 1b "Why did Shakespeare always write in pen?"
    m 3b "Pencils were confusing to him. 2B or not 2B?"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_booknovelideas",
            prompt="Novel",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_booknovelideas:
    m 2a "What do you say to a book that has good plans?"
    m 4l "You say he has some novel ideas!"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_confidentbook",
            prompt="Confident",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_confidentbook:
    m 1a "What made the book so confident?"
    m 3b "He had everything covered!"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_booklove",
            prompt="Book Love",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_booklove:
    m 1a "How do you know when two books are in love?"
    m 4j "They're very font of each other."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_smartbookworm",
            prompt="Bookworm"
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_smartbookworm:
    m 1a "Why couldn't they trick the bookworm?"
    m 2b "Because he could read between the lines."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_booknovelideas",
            prompt="Busy Novelist",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_bookednovelist:
    m 2a "Why was the novelist so busy?"
    m 2k "Because he was booked!"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_soccernogoal",
            prompt="Soccer",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_soccernogoal:
    m 1a "I've talked to people that quit soccer."
    m 4j "They tell me they lost their goal in life."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_stepupyourgamecompetition",
            prompt="Stair Climbing",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_stepupyourgamecompetition:
    m 1a "I was competing for a stair cimbling competition."
    m 3e "I had to step up my game to win."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_skiingdownhill",
            prompt="Skiing",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_skiingdownhill:
    m 1a "It's been a long time since I last went skiing."
    m 2k "I believe my skills are going downhill."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_unbeatablewall",
            prompt="Tennis"
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_unbeatablewall:
    m 1a "The depressing thing about tennis is that no matter how good you get."
    m 4n "You'll never be as good as a wall."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_olympicprocrastination",
            prompt="Olympics"
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_olympicprocrastination:
    m 1a "If procrastination was an Olympic sport."
    m 3l "I would compete in it later! Ehehe~"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_pooldonation",
            prompt="Donations"
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_pooldonation:
    m 2a "One day a man knocked on my door."
    m 3a "He asked for a small donation for the local swimming pool."
    m 3j "So I gave him a glass of water!"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_flippingoutgymnast",
            prompt="Gymnast",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_flippingoutgymnast:
    m 2a "What does a gymnast do when they're angry?"
    m 4b "They flip out!"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_marathonforeducation",
            prompt="Education",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_marathonforeducation:
    m 3a"Why does someone who runs marathons make a good student?"
    m 2j "Because education pays off in the long run!"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_wetdribbled",
            prompt="Basketball",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_wetdribbled:
    m 3a "How did the basketball court get wet?"
    m 4e "Players dribbled all over it!"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_jographysubject",
            prompt="Geography",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_jographysubject:
    m 4a "What's a runner's favorite subject in school?"
    m 4k "Jog-graphy!"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_changingrooms",
            prompt="Football Grounds"
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_changingrooms:
    m 2a "What part of a football ground's never the same?"
    m 2j "The changing rooms."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_volleyballserving",
            prompt="Volleyball",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_volleyballserving:
    m 2a "What can you serve but never eat?"
    m 3k "A volley ball!"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_samepagebooks",
            prompt="Books",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_samepagebooks:
    m 3a "What did one book say to the other one?"
    m 4b "I just wanted to see if we're on the same page!"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_nowordsindictionary",
            prompt="Dictionary",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_nowordsindictionary:
    m 4a "A father gives his son a really cheap dictionary for his birthday."
    m 4k "The son couldn't find the words to thank him!"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_favoriteauthornowriter",
            prompt="Favorite Author"
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_favoriteauthornowriter:
    m 2a "A teacher asks her student 'Who's your favorite author?'"
    m "The student replies 'George Washington!'"
    m 2b "The teacher quickly says 'But he never wrote any books.'"
    m "The student answers saying 'You got it!'."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_abigarithmeticproblem",
            prompt="Arithmetic",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )

label m_joke_abigarithmeticproblem:
    m 4a "What did one arithmetic book say to the other?"
    m 4j "I've got a big problem!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_ghosthomework",
            prompt="Ghost Homework",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_ghosthomework:
    m 3e "Where do young ghosts write their homework?"
    m 1k "Exorcise books!"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_biggestliar",
            prompt="Liar",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_biggestliar:
    m 1a "Who's the biggest liar in a city?"
    m 3j "The lie-brarian."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_binarytypes",
            prompt="Binary",
            category=[store.masjokes.TYPE_CS]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_binarytypes:
    m 4a "There're 10 types of people on the world."
    m 4e "Those who understand binary and those who don't."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_mymosthatedsnake",
            prompt="Snake",
            category=[store.masjokes.TYPE_CS, store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_mymosthatedsnake:
    m 1a "What's the snake I hate the most?"
    m 3b "Python!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_natski",
            prompt="Ski Trip",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_natski:
    m 2a "Why did Natsuki skip the ski trip?"
    m 4l "She could natsuki!"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_programmerwithoutarrays",
            prompt="Arrays",
            category=[store.masjokes.TYPE_CS, store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_programmerwithoutarrays:
    m 2a "Why did the programmer quit his job?"
    m 3b "He couldn't get arrays!"
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_renpie",
            prompt="Pie",
            category=[store.masjokes.TYPE_CS, store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_renpie:
    m 4a "What's my favorite pie flavor?"
    m 4b "Renpy."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_moosician",
            prompt="Musician",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )

label m_joke_moosician:
    m 1a "What do you call a cow that plays the piano?"
    m 1k "A moo-sician."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_lockedpiano",
            prompt="Piano Keys",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_lockedpiano:
    m 3a "Why're pianos so hard to open?"
    m 3e "Because the keys are inside."
    return
    
init 5 python:
    addEvent(
        Event(
            persistent.jokes_database,
            "m_joke_debait",
            prompt="Fishing",
            category=[store.masjokes.TYPE_PUN]
        ),
        eventdb=store.masjokes.jokes_m2p_db
    )
    
label m_joke_debait:
    m 1b "How do you catch a fish?"
    m 1k "Debait!"
    return
