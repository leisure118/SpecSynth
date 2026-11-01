#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int unknown();
int main()
{
  unsigned int N_LIN=1;
  unsigned int N_COL=1;      
  unsigned int j,k;
  int matriz[1][1], maior;
  maior = unknown();
  /*@
    loop invariant 0 <= j <= N_COL;
    loop invariant \forall integer a, b; 0 <= a < j && 0 <= b < N_LIN ==> matriz[a][b] <= maior;
    loop assigns j, k, maior, matriz[0][0];
    loop variant N_COL - j;
  */
  for(j=0;j<N_COL;j++)
    /*@
      loop invariant 0 <= k <= N_LIN;
      loop invariant \forall integer m; 0 <= m < k ==> matriz[j][m] <= maior;
      loop invariant \forall integer a, b; 0 <= a < j && 0 <= b < N_LIN ==> matriz[a][b] <= maior;
      loop assigns k, maior, matriz[j][0];
      loop variant N_LIN - k;
    */
    for(k=0;k<N_LIN;k++)
    {       
       matriz[j][k] = unknown();
       if(matriz[j][k]>=maior)
          maior = matriz[j][k];                          
    }                       
  //@ assert(matriz[0][0]<=maior);    
  return 0;
}
