#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 100
#define fun bor
#include <assert.h>
/*@
  requires \valid_read(x + (0 .. N-1));
  assigns \nothing;
  ensures \result == \at(x[0], Pre) | \at(x[1], Pre) | \at(x[2], Pre) | \at(x[3], Pre) |
                      \at(x[4], Pre) | \at(x[5], Pre) | \at(x[6], Pre) | \at(x[7], Pre) |
                      \at(x[8], Pre) | \at(x[9], Pre) | \at(x[10], Pre) | \at(x[11], Pre) |
                      \at(x[12], Pre) | \at(x[13], Pre) | \at(x[14], Pre) | \at(x[15], Pre) |
                      \at(x[16], Pre) | \at(x[17], Pre) | \at(x[18], Pre) | \at(x[19], Pre) |
                      \at(x[20], Pre) | \at(x[21], Pre) | \at(x[22], Pre) | \at(x[23], Pre) |
                      \at(x[24], Pre) | \at(x[25], Pre) | \at(x[26], Pre) | \at(x[27], Pre) |
                      \at(x[28], Pre) | \at(x[29], Pre) | \at(x[30], Pre) | \at(x[31], Pre) |
                      \at(x[32], Pre) | \at(x[33], Pre) | \at(x[34], Pre) | \at(x[35], Pre) |
                      \at(x[36], Pre) | \at(x[37], Pre) | \at(x[38], Pre) | \at(x[39], Pre) |
                      \at(x[40], Pre) | \at(x[41], Pre) | \at(x[42], Pre) | \at(x[43], Pre) |
                      \at(x[44], Pre) | \at(x[45], Pre) | \at(x[46], Pre) | \at(x[47], Pre) |
                      \at(x[48], Pre) | \at(x[49], Pre) | \at(x[50], Pre) | \at(x[51], Pre) |
                      \at(x[52], Pre) | \at(x[53], Pre) | \at(x[54], Pre) | \at(x[55], Pre) |
                      \at(x[56], Pre) | \at(x[57], Pre) | \at(x[58], Pre) | \at(x[59], Pre) |
                      \at(x[60], Pre) | \at(x[61], Pre) | \at(x[62], Pre) | \at(x[63], Pre) |
                      \at(x[64], Pre) | \at(x[65], Pre) | \at(x[66], Pre) | \at(x[67], Pre) |
                      \at(x[68], Pre) | \at(x[69], Pre) | \at(x[70], Pre) | \at(x[71], Pre) |
                      \at(x[72], Pre) | \at(x[73], Pre) | \at(x[74], Pre) | \at(x[75], Pre) |
                      \at(x[76], Pre) | \at(x[77], Pre) | \at(x[78], Pre) | \at(x[79], Pre) |
                      \at(x[80], Pre) | \at(x[81], Pre) | \at(x[82], Pre) | \at(x[83], Pre) |
                      \at(x[84], Pre) | \at(x[85], Pre) | \at(x[86], Pre) | \at(x[87], Pre) |
                      \at(x[88], Pre) | \at(x[89], Pre) | \at(x[90], Pre) | \at(x[91], Pre) |
                      \at(x[92], Pre) | \at(x[93], Pre) | \at(x[94], Pre) | \at(x[95], Pre) |
                      \at(x[96], Pre) | \at(x[97], Pre) | \at(x[98], Pre) | \at(x[99], Pre);
*/
int bor (int x[N])
{
  int i;
  long long res;
  res = x[0];
  for (i = 1; i < N; i++) {
    res = res | x[i];
  }
  return res;
}
int main ()
{
  int x[N];
  int temp;
  int ret;
  int ret2;
  int ret5;
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  ret2 = fun(x);
  temp=x[0];
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
