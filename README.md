# Complex Networks Coursework subject Software robustness

__Structural Robustness of Operating Systems vs. Applications: A comparative analysis of the Linux Kernel source dependency graph and the Java JDK class dependency graph.__

We are trying to answer wether __the Linux kernel architecture is more resilient to key-file corruption than a standard user application?__

## Subquestions

- Comparing Linux Kernel vs JDK is interesting because of different paradigms / philosophies to developing
- Linux kernel is in C, procedular attempting to mimic OOP (ish)
    - expect high level controler functions calling many smaller utility functions
    
- Java OOP, logic is driven by interacting objects, expect encapsulation and reduced dependencies

Does the strict class hierarchy of Java actually result in more modular network than C or does it create a different level of complexity, e.g God Classes

- Why choose JDK?
    1. OS of java word, most direct equivalent
    2. Internal structure of javca itself
    3. JDK should have high assortativity, Linux should be mixed
    4. Data available


- Could also choose android,
    - Java layer than runs on top of linux
    - Java answer to linux kernel

- Comparing functions to classes is too hard due to number of functions so we compare Files to Classes, as C files tend to be grouped together to perform certain tasks, acting as CLASSES


## Lit Survey Search terms
- Software systems as complex networks
- Small world phenomemon in software
- Software robustness



## Attack types

__1. Random attack__

- Remove nodes at random, check size of largest cluster, repeat until network breaks

__2. Targeted attack__

- Delete highest degree nodes (God classes)
- Expect software to be fragile to targeted attacks



