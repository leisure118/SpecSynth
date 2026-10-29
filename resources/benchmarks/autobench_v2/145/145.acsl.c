int unknown1();
int unknown2();


int main(int flag)
{
  int t = 0;
  int s = 0;
  int a = 0;
  int b = 0;
  /*@
    loop invariant a == b;
    loop invariant a >= 0;
    loop invariant s >= 0;
    loop invariant t >= 0;
    loop invariant (flag == 0) ==> (s == t);
    loop invariant (flag != 0) ==> (t == 2*s);
    loop assigns a, b, s, t;
  */
  while(unknown1()) {
    a++;
    b++;
    s += a;
    t += b;
    if(flag) {
      t += a;
    }
  } 
  //2s >= t
  int x = 1;
  if(flag) {
    x = t - 2*s + 2;
  }
  //x <= 2
  int y = 0;
  // invariant (x <= 2 && y <= x + 2)
  /*@
    loop invariant y >= 0;
    loop invariant y <= x + 2;
    loop invariant x <= 2;
    loop assigns y;
    loop variant x + 2 - y;
  */
  while(y <= x){
    if(unknown2()) 
       y++;
    else 
       y += 2;
  }
  //@ assert(y <= 4);
}

