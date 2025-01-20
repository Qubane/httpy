tags:general
title:Now able to Read News!
description:You are now able to read the news articles!

# Wow!
Yes, indeed, finally you are able to open these news posts and actually read what's inside them!

## What took so long?
It took a long time due to nature of the web server, it being made from very scratch.
Basically this entire web server is just remaking of the wheel, because besides remaking just the serving part,
I am remaking the database part, for storing and serving the news posts, which takes some time to think
on how to make it look ok'ish in code.

## Is it at least secure?
A very good question to ask, and the answer to that is - I don't know.
The way I implemented the access, is to predefine all paths that will be accessed, only use them, and never
directly use user input to access anything.

Is there a gap somewhere? maybe, I can't pay attention to all things at the same time, so I may forget something,
if you do find a vulnerability, notify *@qubane* in discord or at GitHub *UltraQbik/httpy* issues section
