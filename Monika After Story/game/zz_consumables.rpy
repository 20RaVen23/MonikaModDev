#TODO: Update scripts to transfer given consumables (coffee/hotchoc)
#TODO: Delete the following vars:
#   - persistent._mas_acs_enable_coffee
#   - persistent._mas_coffee_been_given
#   - persistent._mas_acs_enable_hotchoc
#   - persistent._mas_c_hotchoc_been_given
#TODO: Stock existing users with some coffee/hotchoc
#TODO: Generic food labels

default persistent._mas_current_consumable = {
    0: {
        "prep_time": None,
        "consume_time": None,
        "id": None,
    },
    1: {
        "prep_time": None,
        "consume_time": None,
        "id": None
    }
}

default persistent._mas_consumable_map = dict()

init python in mas_consumables:
    #Consumable types for sorting in the consumable map
    TYPE_DRINK = 0
    TYPE_FOOD = 1

    #Dict of dicts:
    #consumable_map = {
    #   0: {"consumable_id": MASConsumable},
    #   1: {"consumable_id": MASConsumableFood}
    #}
    consumable_map = dict()


init 10 python:
    #MASConsumable class
    class MASConsumable():
        """
        Consumable class

        PROPERTIES:
            consumable_id - id of the consumable
            disp_name - friendly name for this consumable
            container - the container of this consumable (cup, mug, glass, bottle, etc)
            start_end_tuple_list - list of (start_hour, end_hour) tuples
            acs - MASAccessory to display for the consumable
            split_list - list of split hours
            late_entry_list - list of integers storing the hour which would be considered a late entry
            max_re_serve - amount of times Monika can get a re-serving of this consumable
            cons_chance - likelihood of Monika to keep having this consumable
            prep_low - bottom bracket of preparation time
            prep_high - top bracket of preparation time
            cons_low - bottom bracket of consumable time
            cons_high - top bracket of consumable time
            done_cons_until - the time until Monika can randomly have this consumable again
            get_cons_evl - evl to use for getting the consumable (no prep)
            finish_prep_evl - evl to use when finished preparing a consumable
            finish_cons_evl - evl to use when finished having a consumable
        """

        #Constants:
        BREW_FINISH_EVL = "mas_finished_brewing"
        DRINK_FINISH_EVL = "mas_finished_drinking"
        DRINK_GET_EVL = "mas_get_drink"

        PREP_FINISH_EVL = "mas_finished_prepping"
        FOOD_FINISH_EVL = "mas_finished_eating"
        FOOD_GET_EVL = "mas_get_food"

        DEF_DONE_CONS_TD = datetime.timedelta(hours=2)

        def __init__(
            self,
            consumable_id,
            consumable_type,
            disp_name,
            container,
            start_end_tuple_list,
            acs,
            split_list,
            late_entry_list=None,
            max_re_serve=None,
            cons_chance=80,
            cons_low=10*60,
            cons_high=2*3600,
            prep_low=2*60,
            prep_high=4*60,
            get_cons_evl=None,
            finish_prep_evl=None,
            finish_cons_evl=None
        ):
            """
            MASConsumable constructor

            IN:
                consumable_id - id for the consumable
                    NOTE: Must be unique

                consumable_type - type of consumable:
                    0 - Drink
                    1 - Food

                disp_name - Friendly diaply name (for use in dialogue)

                container - containment for this consumable (cup/mug/bottle/etc)

                start_end_tuple_list - list of tuples storing (start_hour, end_hour)

                late_entry_list - list of times storing when we should load in with a consumable already out

                max_re_serve - amount of times Monika can get a refill of this consumable
                    (Default: None)

                acs - MASAccessory object for this consumable

                split_list - list of split hours for prepping

                cons_chance - chance for Monika to continue having this consumable
                    (Default: 80/100)

                cons_low - low bracket for Monika to have this consumable
                    (Default: 10 minutes)

                cons_high - high bracket for Monika to have this consumable
                    (Default: 2 hours)

                prep_low - low bracket for prep time
                    (Default: 2 minutes)
                    NOTE: If set to None, this will not be considered preppable

                prep_high - high bracket for prep time
                    (Default: 4 minutes)
                    NOTE: If set to None, this will not be considered preppable

                get_cons_evl - evl to use for getting the consumable. If None, a generic is assumed
                    (Default: None)

                finish_prep_evl - evl to use when finished prepping. If None, a generic is assumed
                    (Default: None)

                finish_cons_evl - evl to use when finished prepping. If None, a generic is assumed
                    (Default: None)
            """
            if (
                consumable_type in store.mas_consumables.consumable_map
                and consumable_id in store.mas_consumables.consumable_map[consumable_type]
            ):
                raise Exception("consumable {0} already exists.".format(consumable_id))

            self.consumable_id=consumable_id
            self.consumable_type=consumable_type
            self.disp_name=disp_name
            self.start_end_tuple_list=start_end_tuple_list
            self.acs=acs
            self.cons_chance=cons_chance
            self.cons_low=cons_low
            self.cons_high=cons_high

            if late_entry_list is None:
                self.late_entry_list=[]

                for start, end in start_end_tuple_list:
                    self.late_entry_list.append(start)
            else:
                self.late_entry_list=late_entry_list

            self.max_re_serve=max_re_serve
            self.re_serves_had=0

            self.container=container
            self.split_list=split_list
            self.prep_low=prep_low
            self.prep_high=prep_high

            #EVLs:
            if consumable_type == 0:
                self.get_cons_evl = get_cons_evl if get_cons_evl is not None else MASConsumable.DRINK_GET_EVL
                self.finish_prep_evl = finish_prep_evl if finish_prep_evl is not None else MASConsumable.BREW_FINISH_EVL
                self.finish_cons_evl = finish_cons_evl if finish_cons_evl is not None else MASConsumable.DRINK_FINISH_EVL
            else:
                self.get_cons_evl = get_cons_evl if get_cons_evl is not None else MASConsumable.FOOD_GET_EVL
                self.finish_prep_evl = finish_prep_evl if finish_prep_evl is not None else MASConsumable.PREP_FINISH_EVL
                self.finish_cons_evl = finish_cons_evl if finish_cons_evl is not None else MASConsumable.FOOD_FINISH_EVL

            #Timeout prop
            self.done_cons_until=None

            #Add this to the map
            if consumable_type not in store.mas_consumables.consumable_map:
                store.mas_consumables.consumable_map[consumable_type] = dict()

            store.mas_consumables.consumable_map[consumable_type][consumable_id] = self

            #Now we need to set up data if not already set
            if consumable_id not in persistent._mas_consumable_map:
                persistent._mas_consumable_map[consumable_id] = {
                    "enabled": False,
                    "times_had": 0,
                    "servings_left": 0
                }

        def enabled(self):
            """
            Checks if this consumable is enabled

            OUT:
                boolean:
                    - True if this consumable is enabled
                    - False otherwise
            """
            return persistent._mas_consumable_map[self.consumable_id]["enabled"]

        def enable(self):
            """
            Enables the consumable
            """
            persistent._mas_consumable_map[self.consumable_id]["enabled"] = True

        def disable(self):
            """
            Disables the consumable
            """
            persistent._mas_consumable_map[self.consumable_id]["enabled"] = False

        def increment(self):
            """
            Increments the amount of times Monika has had the consumable
            """
            persistent._mas_consumable_map[self.consumable_id]["times_had"] += 1

        def shouldHave(self, _now=None):
            """
            Checks if we should have this consumable now

            CONDITIONS:
                1. We're within the consumable time range
                2. We pass the chance check to have this consumable
                3. We have not met/exceeded the maximum re-serve amount

            IN:
                _now - datetime.datetime to check if we're within the timerange for this consumable
                If None, now is assumed
                (Default: None)

            OUT:
                boolean:
                    - True if we should have this consumable (passes above conditions)
                    - False otherwise

            NOTE: This does NOT anticipate splits/preparation
            """
            #First, let's check if we've reached the max re-serve point
            if self.max_re_serve is not None and self.re_serves_had == self.max_re_serve:
                return False

            if _now is None:
                _now = datetime.datetime.now()

            _chance = random.randint(1, 100)

            for start_time, end_time in self.start_end_tuple_list:
                if start_time <= _now.hour < end_time and _chance <= self.cons_chance:
                    return True
            return False

        def hasServing(self):
            """
            Checks if we have a serving of this consumable in order to use it

            OUT:
                boolean:
                    - True if we have at least 1 serving left of the consumable
                    - False otherwise
            """
            return persistent._mas_consumable_map[self.consumable_id]["servings_left"] > 0

        def restock(self, servings=100):
            """
            Adds more servings of the consumable

            IN:
                servings - amount of servings to add
                (Default: 100)
            """
            persistent._mas_consumable_map[self.consumable_id]["servings_left"] += servings

        def getStock(self):
            """
            Gets the amount of servings left of a consumable

            OUT:
                integer:
                    - The amount of servings left for the consumable
            """
            return persistent._mas_consumable_map[self.consumable_id]["servings_left"]

        def use(self, amount=1):
            """
            Uses a serving of this consumable

            IN:
                amount - amount of servings to use up
                (Default: 1)
            """
            servings_left = persistent._mas_consumable_map[self.consumable_id]["servings_left"]

            if servings_left - amount < 0:
                persistent._mas_consumable_map[self.consumable_id]["servings_left"] = 0
            else:
                persistent._mas_consumable_map[self.consumable_id]["servings_left"] -= amount

        def re_serve(self):
            """
            Increments the re-serve count
            """
            self.re_serves_had += 1

        def isLateEntry(self, _now=None):
            """
            Checks if we should load with a consumable already out or not

            IN:
                _now - datetime.datetime to check if we're within the time for the consumable
                If None, now is assumed
                (Default: None)

            OUT:
                boolean:
                    - True if we should load in with consumable already out
                    - False otherwise
            """
            if _now is None:
                _now = datetime.datetime.now()

            for index in range(len(self.start_end_tuple_list)):
                #Bit of setup
                _start, _end = self.start_end_tuple_list[index]
                late_hour = self.late_entry_list[index]

                if (
                    _start <= _now.hour < _end
                    and _now.hour >= late_hour
                ):
                    return True
            return False

        def prepare(self, _start_time=None):
            """
            Starts preparing the consumable
            (Sets up the finished preparing event)

            IN:
                _start_time - time to start prepping. If none, now is assumed
            """
            if _start_time is None:
                _start_time = datetime.datetime.now()

            #Start prep
            persistent._mas_current_consumable[self.consumable_type]["prep_time"] = _start_time

            #Calculate end prep time
            end_prep = random.randint(self.prep_low, self.prep_high)

            #Setup the event conditional
            prep_ev = mas_getEV(self.finish_prep_evl)
            prep_ev.conditional = (
                "persistent._mas_current_consumable[{0}]['prep_time'] is not None "
                "and (datetime.datetime.now() - "
                "persistent._mas_current_consumable[{0}]['prep_time']) "
                "> datetime.timedelta(0, {1})"
            ).format(self.consumable_type, end_prep)
            prep_ev.action = EV_ACT_QUEUE

            #Now we set what we're having
            persistent._mas_current_consumable[self.consumable_type]["id"] = self.consumable_id

        def have(self, _start_time=None, skip_leadin=False):
            """
            Allows Monika to have this consumable
            (Sets up the finished consumable event)

            IN:
                _start_time - time to start prepping. If none, now is assumed
                skip_leadin - whether or not we should push the event where Monika gets something to have
            """
            if _start_time is None:
                _start_time = datetime.datetime.now()

            #Delta for having this cons
            consumable_time = datetime.timedelta(0, random.randint(self.cons_low, self.cons_high))

            #Setup the stop time for the cup
            persistent._mas_current_consumable[self.consumable_type]["consume_time"] = _start_time + consumable_time

            #Setup the event conditional
            cons_ev = mas_getEV(self.finish_cons_evl)
            cons_ev.conditional = (
                "persistent._mas_current_consumable[{0}]['consume_time'] is not None "
                "and datetime.datetime.now() > persistent._mas_current_consumable[{0}]['consume_time']"
            ).format(self.consumable_type)
            cons_ev.action = EV_ACT_QUEUE

            #Skipping leadin? We need to set this to persistent and wear the acs for it
            if skip_leadin:
                persistent._mas_current_consumable[self.consumable_type]["id"] = self.consumable_id
                monika_chr.wear_acs_pst(self.acs)

            #If this isn't a prepable type and we don't have a current consumable of this type, we should push the ev
            elif not self.prepable() and not MASConsumable.__getCurrentConsumable(self.consumable_type):
                persistent._mas_current_consumable[self.consumable_type]["id"] = self.consumable_id
                pushEvent(self.get_cons_evl)

            #Increment cup count
            self.increment()

        def isStillPrep(self, _now):
            """
            Checks if we're still prepping something of this type

            IN:
                _now - datetime.datetime object representing current time

            OUT:
                boolean:
                    - True if we're still prepping something
                    - False otherwise
            """
            _time = persistent._mas_current_consumable[self.consumable_type]["prep_time"]
            return (
                _time is not None
                and _time.date() == _now.date()
                and self.isDrinkTime(_time)
            )

        def isStillCons(self, type, _now=None):
            """
            Checks if we're still having something

            IN:
                type - Type of consumable to check for
                    0 - Drink
                    1 - Food

                _now - datetime.datetime object representing current time
                    If none, now is assumed
                    (Default: None)

            OUT:
                boolean:
                    - True if we're still having something
                    - False otdherwise
            """
            if _now is None:
                _now = datetime.datetime.now()

            _time = persistent._mas_current_consumable[self.consumable_type]["consume_time"]
            return _time is not None and _now < _time

        def isConsTime(self, _now=None):
            """
            Checks if we're in the time range for this consumable

            IN:
                _now - datetime.datetime to check if we're within the time for
                    If None, now is assumed
                    (Default: None)

            OUT:
                boolean:
                    - True if we're within the consumable time(s) of this consumable
                    - False otherwise
            """
            if _now is None:
                _now = datetime.datetime.now()

            for start_time, end_time in self.start_end_tuple_list:
                if start_time <= _now.hour < end_time:
                    return True
            return False

        def shouldPrep(self, _now=None):
            """
            Checks if we're in the time range for this consumable and we should prepare it

            IN:
                _time - datetime.datetime to check if we're within the time for
                    If none, now is assumed
                    (Default: None)

            OUT:
                boolean:
                    - True if we're within the preparation time(s) of this consumable (and consumable is preparable)
                    - False otherwise
            """
            if not self.prepable():
                return False

            if _now is None:
                _now = datetime.datetime.now()

            _chance = random.randint(1, 100)

            for split in self.split_list:
                if _now.hour < split and _chance <= self.cons_chance:
                    return True
            return False

        def prepable(self):
            """
            Checks if this consumable is preparable

            OUT:
                boolean:
                    - True if this consumable has:
                        1. prep_high
                        2. prep_low

                    - False otherwise
            """
            return self.prep_low is not None and self.prep_high is not None

        def checkCanHave(self, _now=None):
            """
            Checks if we can have this consumable again

            IN:
                _now - datetime.datetime to check against
                    If None, now is assumed
                    (Default: None)

            OUT:
                boolean:
                    - True if we can have this consumable
                    - False otherwise
            """
            #First, if this is None, we return True
            if self.done_cons_until is None:
                return True

            #Otherwise, we need to do a comparison
            elif _now is None:
                _now = datetime.datetime.now()

            if _now >= self.done_cons_until:
                self.done_cons_until = None
                return True
            return False

        @staticmethod
        def _reset():
            """
            Resets the events for the consumable and resets the current consumable(s)
            """
            def cons_reset(consumable):
                """
                Resets the labels for the current consumables

                IN:
                    consumable - consumable object to reset
                """
                if consumable is None:
                    return

                monika_chr.remove_acs(consumable.acs)
                consumable.re_serves_had = 0

                #Get evs
                get_ev = mas_getEV(consumable.get_cons_evl)
                prep_ev = mas_getEV(consumable.finish_prep_evl)
                cons_ev = mas_getEV(consumable.finish_cons_evl)

                #Reset the events
                get_ev.conditional = None
                cons_ev.action = None
                prep_ev.conditional = None
                prep_ev.action = None
                cons_ev.conditional = None
                cons_ev.action = None

                #And remove them from the event list
                mas_rmEVL(consumable.get_cons_evl)
                mas_rmEVL(consumable.finish_prep_evl)
                mas_rmEVL(consumable.finish_cons_evl)

                #Now reset the persist var for this type
                persistent._mas_current_consumable[consumable.consumable_type] = {
                    "prep_time": None,
                    "consume_time": None,
                    "id": None
                }

            #Get current consumables and reset
            cons_reset(MASConsumable._getCurrentDrink())
            cons_reset(MASConsumable._getCurrentFood())

        @staticmethod
        def _getCurrentDrink():
            """
            Gets the MASConsumable object for the current drink or None if we're not drinking

            OUT:
                - Current MASConsumable if drinking
                - None if not drinking
            """
            return MASConsumable.__getCurrentConsumable(store.mas_consumables.TYPE_DRINK)

        @staticmethod
        def _getCurrentFood():
            """
            Gets the MASConsumable object for the current food or None if we're not eating

            OUT:
                - Current MASConsumable if eating
                - None if not eating
            """
            return MASConsumable.__getCurrentConsumable(store.mas_consumables.TYPE_FOOD)

        @staticmethod
        def _isHaving(_type):
            """
            Checks if we're currently drinking something right now

            IN:
                _type - integer representing the consumable type

            OUT:
                boolean:
                    - True if we have a current consumable of _type and consume time
                    - False otherwise
            """
            return (
                persistent._mas_current_consumable[_type]["id"]
                and persistent._mas_current_consumable[_type]["consume_time"]
            )

        @staticmethod
        def _getConsumablesForTime(_type, _now=None):
            """
            Gets a list of all consumable drinks active at this time

            IN:
                _type - type of consumables to get
                _now - datetime.datetime object representing current time
                    If None, now is assumed
                    (Default: None)

            OUT:
                list of consumable objects of _type enabled and within time range
            """
            if _type not in store.mas_consumables.consumable_map:
                return []

            return [
                cons
                for cons in mas_consumables.consumable_map[_type].itervalues()
                if cons.enabled() and cons.hasServing() and cons.checkCanHave() and cons.isConsTime()
            ]

        @staticmethod
        def _validatePersistentData(_type):
            """
            Verifies that the data stored in persistent._mas_current_consumable is valid to the consumables currently set up

            IN:
                _type - type of consumable to validate persistent data for

            NOTE: If the persistent data stored isn't valid, it is reset.
            """
            if MASConsumable._isHaving(_type) and not MASConsumable.__getCurrentConsumable(_type):
                persistent._mas_current_consumable[_type] = {
                    "prep_time": None,
                    "consume_time": None,
                    "id": None
                }

        @staticmethod
        def _checkConsumables(startup=False):
            """
            Logic to handle Monika having a consumable both on startup and during runtime

            IN:
                startup - Whether or not we should check for a late entry
                (Default: False)
            """
            MASConsumable.__checkingLogic(
                _type=store.mas_consumables.TYPE_DRINK,
                curr_cons=MASConsumable._getCurrentDrink(),
                startup=startup
            )

            MASConsumable.__checkingLogic(
                _type=store.mas_consumables.TYPE_FOOD,
                curr_cons=MASConsumable._getCurrentDrink(),
                startup=startup
            )

            if startup:
                MASConsumable._absentUse()

        @staticmethod
        def _absentUse():
            """
            Runs a check on all consumables and subtracts the amount used in the player's absence
            """
            def calculate_and_use(consumable, servings, days_absent):
                """
                Checks how many servings of the consumable Monika will have used in the player's absence

                IN:
                    consumable - consumable to use
                    servings - amount of servings per having of the consumable
                    days_absent - amount of days the player was absent
                """
                chance = random.randint(1, 100)
                for day in range(days_absent):
                    if chance <= consumable.cons_chance:
                        consumable.use(servings)


            consumables = MASConsumable._getEnabledConsumables()
            _days = mas_getAbsenceLength().days

            for cons in consumables:
                if cons.prepable():
                    calculate_and_use(consumable=cons, servings=7, days_absent=_days)
                else:
                    calculate_and_use(consumable=cons, servings=4, days_absent=_days)

        @staticmethod
        def _getEnabledConsumables():
            """
            Gets all enabled consumables

            OUT:
                List of MASConsumable objects which are enabled

            NOTE: enabled is regardless of stock amount
            """
            consumables = []

            if store.mas_consumables.TYPE_DRINK in store.mas_consumables.consumable_map:
                consumables.extend([
                    drink
                    for drink in store.mas_consumables.consumable_map[mas_consumables.TYPE_DRINK].values()
                    if drink.enabled()
                ])

            if store.mas_consumables.TYPE_FOOD in store.mas_consumables.consumable_map:
                consumables.extend([
                    food
                    for food in store.mas_consumables.consumable_map[mas_consumables.TYPE_FOOD].values()
                    if food.enabled()
                ])

            return consumables

        @staticmethod
        def __getCurrentConsumable(_type):
            """
            Gets the current consumable, provided by type

            IN:
                _type - consumable type to get the current consumable for

            OUT:
                MASConsumable object representing the current consumable object for the type
                If there's no consumable out by _type, None is returned
            """
            return mas_getConsumable(
                _type,
                persistent._mas_current_consumable[_type]["id"]
            )

        @staticmethod
        def __checkingLogic(_type, curr_cons, startup):
            """
            Generalized logic to check if we should have a consumable

            IN:
                _type - consumable type
                curr_cons - current_consumable (of _type)
                startup - whether or not to perform a startup check
            """
            available_cons = MASConsumable._getConsumablesForTime(_type)

            #Verify persist data
            MASConsumable._validatePersistentData(_type)

            #Wear the acs if we don't have it out for some reason
            if MASConsumable._isHaving(_type) and not monika_chr.is_wearing_acs(curr_cons.acs):
                monika_chr.wear_acs_pst(curr_cons.acs)

            #If we have no consumables, then there's no point in doing anything
            if not available_cons:
                if (
                    MASConsumable._isHaving(_type)
                    and (
                        not curr_cons.isStillCons()
                        and mas_getCurrSeshStart() > persistent._mas_current_consumable[_type]["consume_time"]
                    )
                ):
                    MASConsumable._reset()
                return

            #If we're currently prepping/having anything, we don't need to do anything else
            if persistent._mas_current_consumable[_type]["id"] is not None:
                return

            #Otherwise, step two: what are we having?
            cons = random.choice(available_cons)

            #Setup some vars
            _now = datetime.datetime.now()

            #Time to C O N S U M E
            #First, clear vars so we start fresh
            MASConsumable._reset()

            #First, should we even have this?
            if cons.shouldHave():
                #If we prepare, we prep for 7 chages worth (to acct for multiple servings)
                if cons.prepable():
                    cons.use(amount=7)

                #Otherwise, if it's a non-prepable, just one
                else:
                    cons.use()

                #Are we loading in after the time? If so, we should already have the cons out. No prep, just have
                if startup and cons.isLateEntry():
                    cons.have(skip_leadin=True)

                else:
                    #If this is a prepable, we should prep it
                    if cons.prepable() and cons.shouldPrep(_now):
                        cons.prepare()

                    #Otherwise, we'll just set up having it
                    elif not cons.prepable():
                        cons.have()

#END: MASConsumable class

    #START: Global functions
    def mas_getConsumable(consumable_type, consumable_id):
        """
        Gets a consumable object by type and id

        IN:
            consumable_type - Type of consumable to look for:
                0 - Drink
                1 - Food
            consumable_id - id of the consumable

        OUT:
            Consumable object:
                If found, MASConsumable
                If not found, None
        """
        if consumable_type not in mas_consumables.consumable_map:
            return
        return store.mas_consumables.consumable_map[consumable_type].get(consumable_id)

    def mas_getConsumableDrink(consumable_id):
        """
        Gets the consumable drink by id.

        IN:
            consumable_id - consumable to get

        OUT:
            MASConsumable object if found, None otherwise
        """
        return mas_getConsumable(
            store.mas_consumables.TYPE_DRINK,
            consumable_id
        )

    def mas_getConsumableFood(consumable_id):
        """
        Gets the consumable food by id.

        IN:
            consumable_id - consumable to get

        OUT:
            MASConsumableFood object if found, None otherwise
        """
        return mas_getConsumable(
            store.mas_consumables.TYPE_FOOD,
            consumable_id
        )

#START: consumable drink defs:
init 11 python:
    MASConsumable(
        consumable_id="coffee",
        consumable_type=store.mas_consumables.TYPE_DRINK,
        disp_name="coffee",
        container="cup",
        start_end_tuple_list=[(5, 12)],
        acs=mas_acs_mug,
        split_list=[9],
        late_entry_list=[7]
    )

    MASConsumable(
        consumable_id="hotchoc",
        consumable_type=store.mas_consumables.TYPE_DRINK,
        disp_name="hot chocolate",
        container="cup",
        start_end_tuple_list=[(19,22)],
        acs=mas_acs_hotchoc_mug,
        split_list=[21],
        late_entry_list=[20]
    )

#START: Finished brewing/drinking evs
##Finished brewing
init 5 python:
    import random
    #This event gets its params via _startupDrinkLogic()
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_finished_brewing",
            show_in_idle=True,
            rules={"skip alert": None}
        )
    )

label mas_finished_brewing(consumable):
    $ current_drink = MASConsumable._getCurrentDrink()
    call mas_consumables_generic_finished_prepping(current_drink)
    return


###Drinking done
init 5 python:
    import random
    #Like finshed_brewing, this event gets its params from
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_finished_drinking",
            show_in_idle=True,
            rules={"skip alert": None}
        )
    )

label mas_finished_drinking:
    #Get the current drink and see how we should act here
    $ current_drink = MASConsumable._getCurrentDrink()
    call mas_consumables_generic_finish_having(current_drink)
    return

##Get drink
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_get_drink",
            show_in_idle=True,
            rules={"skip alert": None}
        )
    )

label mas_get_drink:
    $ current_drink = MASConsumable._getCurrentDrink()
    call mas_consumables_generic_get(current_drink)
    return
#END: Generic drink evs

#START: Generic food evs
init 5 python:
    import random
    #This event gets its params via _startupDrinkLogic()
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_finished_prepping",
            show_in_idle=True,
            rules={"skip alert": None}
        )
    )

label mas_finished_prepping(consumable):
    $ current_food = MASConsumable._getCurrentDrink()
    call mas_consumables_generic_finished_prepping(current_food)
    return


###Drinking done
init 5 python:
    import random
    #Like finshed_brewing, this event gets its params from
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_finished_eating",
            show_in_idle=True,
            rules={"skip alert": None}
        )
    )

label mas_finished_eating:
    #Get the current drink and see how we should act here
    $ current_food = MASConsumable._getCurrentDrink()
    call mas_consumables_generic_finish_having(current_food)
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_get_food",
            show_in_idle=True,
            rules={"skip alert": None}
        )
    )

label mas_get_food:
    $ current_food = MASConsumable._getCurrentDrink()
    call mas_consumables_generic_get(current_food)
    return
#END: Generic food evs

#START: Generic consumable labels
label mas_consumables_generic_get(consumable):
    #Moving this here so she uses this line to 'pull her chair back'
    $ curr_zoom = store.mas_sprites.zoom_level
    call monika_zoom_transition_reset(1.0)

    show emptydesk at i11 zorder 9

    if store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 1eua "I'm going to get a [consumable.container] of [consumable.disp_name]. I'll be right back.{w=1}{nw}"

    else:
        m 1eua "I'm going to get a [consumable.container] of [consumable.disp_name]."
        m 1eua "Hold on a moment."

    # monika is off screen
    hide monika with dissolve

    # wrap these statemetns so we can properly add / remove the mug
    $ renpy.pause(1.0, hard=True)
    $ monika_chr.wear_acs_pst(consumable.acs)
    $ renpy.pause(4.0, hard=True)

    show monika 1eua at i11 zorder MAS_MONIKA_Z with dissolve
    hide emptydesk

    # 1 second wait so dissolve is complete before zooming
    $ renpy.pause(0.5, hard=True)
    call monika_zoom_transition(curr_zoom, 1.0)

    if store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 1hua "Back!{w=1.5}{nw}"

    else:
        m 1eua "Okay, what else should we do today?"
    return

label mas_consumables_generic_finish_having(consumable):
    $ get_more = (
        consumable.shouldHave()
        and (consumable.prepable() or (not consumable.prepable() and consumable.hasServing()))
    )

    if (not mas_canCheckActiveWindow() or mas_isFocused()) and not store.mas_globals.in_idle_mode:
        m 1esd "Oh, I've finished my [consumable.disp_name]."

    #Moving this here so she uses this line to 'pull her chair back'
    $ curr_zoom = store.mas_sprites.zoom_level
    call monika_zoom_transition_reset(1.0)

    show emptydesk at i11 zorder 9

    if store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        if get_more:
            #It's drinking time
            m 1eua "I'm going to get some more [consumable.disp_name]. I'll be right back.{w=1}{nw}"

        else:
            m 1eua "I'm going to put this [consumable.container] away. I'll be right back.{w=1}{nw}"

    else:
        if get_more:
            m 1eua "I'm going to get another [consumable.container]."

        m 1eua "Hold on a moment."

    # monika is off screen
    hide monika with dissolve

    # wrap these statemetns so we can properly add / remove the acs
    $ renpy.pause(1.0, hard=True)

    #Should we get some more?
    if not get_more:
        $ MASConsumable._reset()
        #We'll just set up a time when we can have this drink again
        $ consumable.done_cons_until = datetime.datetime.now() + MASConsumable.DEF_DONE_CONS_TD

    else:
        $ consumable.have()
        $ consumable.re_serve()

        #Non-prepables are per refill, so they'll run out a bit faster
        if not consumable.prepable():
            $ consumable.use()

    $ renpy.pause(4.0, hard=True)

    show monika 1eua at i11 zorder MAS_MONIKA_Z with dissolve
    hide emptydesk

    # 1 second wait so dissolve is complete before zooming
    $ renpy.pause(0.5, hard=True)
    call monika_zoom_transition(curr_zoom, 1.0)

    if store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 1hua "Back!{w=1.5}{nw}"

    else:
        m 1eua "Okay, what else should we do today?"
    return

label mas_consumables_generic_finished_prepping(consumable):
    if (not mas_canCheckActiveWindow() or mas_isFocused()) and not store.mas_globals.in_idle_mode:
        m 1esd "Oh, my [consumable.disp_name] is ready."

    #Moving this here so she uses this line to 'pull her chair back'
    $ curr_zoom = store.mas_sprites.zoom_level
    call monika_zoom_transition_reset(1.0)

    #This line is here so it looks better when we hide monika
    show emptydesk at i11 zorder 9

    if store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        #Idle pauses and then progresses on its own
        m 1eua "I'm going to grab some [consumable.disp_name]. I'll be right back.{w=1}{nw}"

    else:
        m 1eua "Hold on a moment."

    #Monika is off screen
    hide monika with dissolve

    #Transition stuffs
    $ renpy.pause(1.0, hard=True)

    #Wear drink acs
    $ monika_chr.wear_acs_pst(consumable.acs)
    #Reset prep time
    $ persistent._mas_current_consumable[consumable.consumable_type]["prep_time"] = None
    #Start drinking
    $ consumable.have()

    $ renpy.pause(4.0, hard=True)

    show monika 1eua at i11 zorder MAS_MONIKA_Z with dissolve
    hide emptydesk

    # 1 second wait so dissolve is complete before zooming
    $ renpy.pause(0.5, hard=True)
    call monika_zoom_transition(curr_zoom, 1.0)

    if store.mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 1hua "Back!{w=1.5}{nw}"

    else:
        m 1eua "Okay, what else should we do today?"
    return