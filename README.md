# unmcg

unmcg: Unique Number MultiCast Generator

An overly complicated, unique number generator that sends messages to each other via multicast with Python2/Jython2

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

# liam@gibson src % python2
# Python 2.7.18 (default, Oct 31 2023, 11:12:53) 
# [GCC Apple LLVM 15.0.0 (clang-1500.0.40.1)] on darwin
# Type "help", "copyright", "credits" or "license" for more information.
# >>> import unmcg
# INFO [Wed May 21 15:17:36 2025]: Starting unmcg threads
# INFO [Wed May 21 15:17:36 2025]: Starting id discovery
# INFO [Wed May 21 15:17:36 2025]: discovery picked id: 407 time: 1747865856937957
# INFO [Wed May 21 15:17:36 2025]: sending multicast message: "discovery ec7a6723638d438c9a702f2d0343857c 1747865856937957 407" to: 224.1.2.3:31173
# INFO [Wed May 21 15:17:36 2025]: listening for multicast data on 224.1.2.3:31173
# INFO [Wed May 21 15:17:37 2025]: sending multicast message: "discovery ec7a6723638d438c9a702f2d0343857c 1747865856937957 407" to: 224.1.2.3:31173
# INFO [Wed May 21 15:17:38 2025]: sending multicast message: "discovery ec7a6723638d438c9a702f2d0343857c 1747865856937957 407" to: 224.1.2.3:31173
# INFO [Wed May 21 15:17:39 2025]: sending multicast message: "discovery ec7a6723638d438c9a702f2d0343857c 1747865856937957 407" to: 224.1.2.3:31173
# INFO [Wed May 21 15:17:40 2025]: sending multicast message: "discovery ec7a6723638d438c9a702f2d0343857c 1747865856937957 407" to: 224.1.2.3:31173
# INFO [Wed May 21 15:17:41 2025]: ID discovery successful, my id is 407
# >>> unmcg.get_id()
# 407
# >>> unmcg.get_number()
# 2505214070000000001L
# >>> unmcg.get_number()
# 2505214070000000002L
# >>> unmcg.get_number()
# 505214070000000003L
# >>> unmcg.get_number()
# 2505214070000000004L
