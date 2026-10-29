#include<limits.h>
int Max_in_Array(int arr[],int n)
{
 int max=arr[0];
 for(int j=0;j<n;j++)
 {
 if(arr[j]>max)
 {
 max=arr[j];
 }
 }
 return max;
}
int main()
{
int n=5;
int arr[]={50,44,33,2,88};
int k=Max_in_Array(arr,n);
//@ assert \forall integer i; 0<=i<n ==> k>=arr[i];
}