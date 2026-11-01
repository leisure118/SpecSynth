#include<limits.h>
int check(int n){
if(n%2==0)
return 1;
else
return 0;
}
int main(){
int a=4;
int r=check(a);
//@assert a==4;
}