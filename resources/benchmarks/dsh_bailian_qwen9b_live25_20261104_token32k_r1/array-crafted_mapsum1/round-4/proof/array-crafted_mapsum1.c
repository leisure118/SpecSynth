#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
#define N 100
#define fun mapsum
#include <assert.h>
/*@
  logic integer mapsum_spec(int *x, integer n) =
    n <= 0 ? 0 : mapsum_spec(x, n-1) + (n-1) + x[n-1];
*/
/*@
  logic integer mapsum_total(int *x) =
    x[0] + x[1] + x[2] + x[3] + x[4] + x[5] + x[6] + x[7] + x[8] + x[9]
    + x[10] + x[11] + x[12] + x[13] + x[14] + x[15] + x[16] + x[17] + x[18] + x[19]
    + x[20] + x[21] + x[22] + x[23] + x[24] + x[25] + x[26] + x[27] + x[28] + x[29]
    + x[30] + x[31] + x[32] + x[33] + x[34] + x[35] + x[36] + x[37] + x[38] + x[39]
    + x[40] + x[41] + x[42] + x[43] + x[44] + x[45] + x[46] + x[47] + x[48] + x[49]
    + x[50] + x[51] + x[52] + x[53] + x[54] + x[55] + x[56] + x[57] + x[58] + x[59]
    + x[60] + x[61] + x[62] + x[63] + x[64] + x[65] + x[66] + x[67] + x[68] + x[69]
    + x[70] + x[71] + x[72] + x[73] + x[74] + x[75] + x[76] + x[77] + x[78] + x[79]
    + x[80] + x[81] + x[82] + x[83] + x[84] + x[85] + x[86] + x[87] + x[88] + x[89]
    + x[90] + x[91] + x[92] + x[93] + x[94] + x[95] + x[96] + x[97] + x[98] + x[99]
    + 4950;
*/
/*@
  requires \valid_read(x + (0 .. N-1));
  assigns \nothing;
  ensures \result == (int)mapsum_total(x);
*/
int mapsum (int x[N])
{
  int i;
  long long ret;
  ret = 0;
  /*@ loop invariant 0 <= i <= N;
      loop invariant ret == mapsum_spec(x, i);
      loop assigns i, ret;
      loop variant N - i;
  */
  for (i = 0; i < N; i++) {
    ret = ret+ i + x[i];
  }
  return ret;
}
int main ()
{
  int x[N];
  int temp;
  int ret;
  int ret2;
  int ret5;
  /*@ loop invariant 0 <= i <= N;
      loop assigns i, x[0 .. N-1];
      loop variant N - i;
  */
  for (int i = 0; i < N; i++) {
    x[i] = unknown();
  }
  ret = fun(x);
  temp=x[0];x[0] = x[1]; x[1] = temp;
  ret2 = fun(x);
  temp=x[0];
  /*@ loop invariant 0 <= i <= N-1;
      loop invariant \forall integer k; i <= k <= N-1 ==> x[k] == \at(x[k], LoopEntry);
      loop invariant mapsum_total(x) - \at(mapsum_total(x), LoopEntry) == \at(x[i], LoopEntry) - \at(x[0], LoopEntry);
      loop assigns i, x[0 .. N-2];
      loop variant (N-1) - i;
  */
  for(int i =0 ; i<N-1; i++){
     x[i] = x[i+1];
  }
  x[N-1] = temp;
  ret5 = fun(x);
  //@ assert !(ret != ret2 || ret !=ret5);
  return 1;
}
