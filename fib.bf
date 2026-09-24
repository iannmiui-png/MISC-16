Fibonacci: counter in c0; a in c1; b in c2; temp in c3
++++++++++ >> + <<          c0 is 10 and b is 1
[ > [->>+<<]                move a into temp
  > [-<+>>+<]               move b into a and temp
  > [-<+>]                  move temp into b
  <<< - ]
> []                        halt on a (which is F of 10)
