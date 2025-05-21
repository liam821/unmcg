# unmcg

unmcg: Unique Number MultiCast Generator

An overly complicated, unique number generator that sends messages to each other via multicast

Thread-safe, multiple instances, and multiple host safe, to generate an ID number

        # 9223372036854775808 max number
        # 2405301200000000045
        # YYMMDDXXXNNNNNNNNNN
        # ^ ^ ^ ^  ^- seq number (0+=1...9999999999) (9.9b max in 24 hours)
        # | | | |---- thread id 1...999 (unique threadid using multicast discovery)
        # | | |------ day
        # | |-------- month
        # |---------- year  
        #
        # example number 2405301200001342768L
