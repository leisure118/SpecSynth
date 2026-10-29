#include<limits.h>
/*@
  requires n >= 1;
  requires \valid(arr+(0..n-1));
  assigns \nothing;
  ensures \forall integer i; 0 <= i < n ==> \result <= arr[i];
*/
int min_in_array(int arr[],int n)
{
 int min=arr[0];
 /*@
   loop invariant 0 <= i <= n;
   loop invariant
   \forall integer j; 0 <= j < i ==> min <= arr[j];
   loop assigns i, min;
   loop variant n - i;
 */
 for(int i=0;i<n;i++)
 {
 if(arr[i]<min)
 {
 min=arr[i];
 }
 }
 return min;
}
int main()
{
int len=5;
int arr[]={5,3,1,33,22};
int k=min_in_array(arr,len);
//@ assert \forall integer i; 0<=i<len ==> k<=arr[i];
return 0;
}