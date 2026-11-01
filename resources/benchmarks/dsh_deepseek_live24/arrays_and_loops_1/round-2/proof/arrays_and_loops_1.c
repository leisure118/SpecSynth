/*@ requires 0 <= base * height <= 2147483647;
    assigns \nothing;
    ensures \result == (base * height) / 2;
*/
int area(int base, int height){
    int res = (base *  height)/2;
    return res;
}
int main() {
    int a = area(4, 5);
    //@ assert a == 10;
}
