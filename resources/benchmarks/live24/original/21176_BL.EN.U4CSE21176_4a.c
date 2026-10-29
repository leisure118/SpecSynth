#include<limits.h>
int check(int n){
if(n%3==0)
return 1;
else
return 0;
}
int main(){
int a=9;
int r=check(a);
//@assert a==9;
}