int func(int a) {
    int x, y;
    int sum, res;
    if (a == 0){
        x = 0; y = 0;
    }
    else {
        x = 5; y = 5;
    }
    sum = x + y; 
    res = 10/sum; 
    return res;
}
int main(){
    int a = 1;
    int result = func(a);
    //@ assert result == 1;
    return 0;
}