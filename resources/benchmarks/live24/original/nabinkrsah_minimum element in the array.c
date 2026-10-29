#include<limits.h>
int min_in_array(int arr[],int n)
{
 int min=arr[0];
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