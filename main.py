# -*- coding: utf-8 -*-
import base64
import json
import logging
import os
import time
from operator import itemgetter
import requests
from requests.adapters import HTTPAdapter

corpid = 'wxd29090e3a46349dd'


class QWschool:
    """ 初灵大学 """

    headers = {
        'Host': 'qy.51vj.cn',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36 QBCore/4.0.1268.400 QQBrowser/9.0.2524.400 Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36 wxwork/3.0.21 (MicroMessenger/6.2) WindowsWechat',
        'Accept': 'application/json;charset=utf-8',
        # 'Referer': '',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN',
        'Cookie': ''
    }

    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update(self.headers)
        self.session.mount('http://', HTTPAdapter(max_retries=3))
        self.session.mount('https://', HTTPAdapter(max_retries=3))
        self.get_home()

    def get_home(self):
        url1 = 'https://qy.51vj.cn/app/home/school?corpid=wxd29090e3a46349dd&appid=1003'
        url2 = 'https://qy.51vj.cn/company/app/config?_=1590762238831&corpid=wxd29090e3a46349dd&appid=1003&hidden=0&filter-visible=true'
        # r = self.session.get(url, verify=False)
        r1 = self.session.get(url1, timeout=10)
        r2 = self.session.get(url2, timeout=10)
        pass

    def study_plan(self, page=1, size=15):
        url = 'https://qy.51vj.cn/microinstitute/study_plan?_={}&corpid={}&appid=35&page={}&size={}'.format(
            self._, corpid, page, size)
        # r = self.session.get(url, verify=False)
        r = self.session.get(url, timeout=10)
        rr = r.json()
        if not rr.get('success'):
            logging.error('course_list()\t{}'.format(r.text))
            return
        return rr

    @property
    def plans(self):
        start_time = time.time()
        plans_ = list()
        total_pages = self.study_plan().get('total_pages')
        for i in range(1, total_pages+1):
            r = self.study_plan(i)
            if r.get('success'):
                logging.info('Get page: {} success'.format(i))
                plans_ += r.get('study_plans')
        for i, plan in enumerate(plans_):
            r = self.course_details(plan.get('course_id'), plan.get('id'))
            if r.get('success'):
                logging.info('Get course: {} {}'.format(i, plan.get('name')))
                plans_[i] = r.get('course')
        plans_ = sorted(plans_, key=itemgetter('duration'))
        with open('stuty_plans.json', 'w') as fp:
            json.dump(plans_, fp)
        end_time = time.time()
        logging.info('Search time：{}s\t{}pages\t{}courses'.format(end_time-start_time, total_pages, len(plans_)))
        return plans_

    def get_courses(self, page=1, size=15):
        url = 'https://qy.51vj.cn/microinstitute/user-study/my_course?_={}&corpid={}&appid=35&parentid=1003&page={}&size={}&name=&type=2'.format(
            self._, corpid, page, size)
        # r = self.session.get(url, verify=False).json()
        r = self.session.get(url, timeout=10)
        rr = r.json()
        if not rr.get('success'):
            logging.error('get_courses()\t{}'.format(r.text))
            return
        return rr

    @property
    def courses(self):
        r = self.get_courses()
        # if not result or not result.get('user_study_new'):
        #     return
        result = r.get('user_study_new')
        if r.get('total_pages') > 1:
            for page in range(2, r.get('total_pages') + 1):
                result += self.get_courses(page).get('user_study_new')
        return result

    def course_details(self, course_id, plan_id):
        url = 'https://qy.51vj.cn/microinstitute/course/{}?_={}&corpid={}&appid=35&parentid=1003&plan_id={}&view=false'.format(
            course_id, self._, corpid, plan_id)
        # r = self.session.get(url, verify=False).json()
        r = self.session.get(url, timeout=10)
        rr = r.json()
        if not rr.get('success'):
            logging.error('course_details()\t{}'.format(r.text))
            return
        return rr

    def get_details(self, courses):
        for i in courses:
            logging.info('{}\t{}课件'.format(i.get('name'), i.get('total_period')))
            if i.get('is_finish'):
                continue
            plan_id = i.get('study_plan_id')
            course_id = i.get('course_id')
            logging.info('{}\t{}'.format(plan_id, course_id))
            r = self.course_details(course_id, plan_id)
            if not r.get('success'):
                pass
            course = r.get('course')
            if course.get('period') == course.get('completed_period'):
                logging.info('{}\t{}'.format(course['name'], '学分到手美滋滋'))
                return
            course = course.get('chapters')[0] if course.get('chapters') else course
            yield plan_id, course_id, course

    def _study(self, ware_id):
        url = 'https://qy.51vj.cn/microinstitute/courseware/{}?_={}&corpid={}&appid=35&parentid=1003'.format(
            ware_id, self._, corpid)
        # r = self.session.get(url, verify=False).json()
        r = self.session.get(url, timeout=10)
        rr = r.json()
        if not rr.get('success'):
            logging.error('_study()\t{}'.format(r.text))
            return
        return rr

    def _add(self, course_id, plan_id):
        query_string = {
            "study_plan_id": str(course_id),
            "course_id": str(plan_id),
        }
        # query_string = '{{"study_plan_id":"{}","course_id":"{}"}}'.format(course_id, plan_id)
        url = 'https://qy.51vj.cn/microinstitute/user-study?_={}&corpid={}&appid=35&parentid=1003'.format(
            self._, corpid)
        # r = self.session.post(url, json=query_string, verify=False).json()
        r = self.session.post(url, json=query_string, timeout=10)
        rr = r.json()
        if not rr.get('success'):
            logging.error('_add()\t{}'.format(r.text))
            return
        return rr

    def _verify(self, course_id, plan_id, ware_id):
        query_string = {
            "study_plan_id": plan_id,
            "course_id": course_id,
            "course_chapter_id": "0",
            "courseware_id": ware_id,
            "duration": 10
        }
        url = 'https://qy.51vj.cn/microinstitute/user-study/record?_={}&corpid={}&appid=35&parentid=1003'.format(
            self._, corpid)
        # r = self.session.post(url, json=query_string, verify=False).json()
        r = self.session.post(url, json=query_string, timeout=10)
        rr = r.json()
        if not rr.get('success'):
            logging.error('_verify()\t{}'.format(r.text))
            return
        return rr

    def user_study(self, course_id, plan_id, ware_id, course, ware):
        study = self._study(ware_id)
        if not study.get('success'):
            logging.error('user_study()\t{} {} {} {}'.format(course_id, plan_id, ware_id, course.get('name')))
            return
        while True:
            try:
                verify = self._verify(course_id, plan_id, ware_id)
                if verify.get('is_complete'):
                    logging.info('Complete: {}'.format(course['name']))
                    return
                study_time = verify.get('study_time')
                if not study_time:
                    logging.info(verify)
                    time.sleep(10)
                    self._study(ware_id)
                    # course = self.course_details(course_id, plan_id)
                    continue
                logging.info('{} 进度{}/{}\t{} {}%'.format(
                    course.get('name'), course.get('completed_period'), course.get('period'), ware['title'],
                    round(study_time / ware['duration'] * 100, 1)))
                time.sleep(10)
            except Exception as e:
                logging.error(e)

    def always_study(self):
        while True:
            try:
                now_time = time.time()
                logging.info('Read study plan: {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now_time))))
                file_time = os.path.getmtime('stuty_plans.json')
                logging.info('File mtime: {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_time))))
                if now_time - file_time > 24 * 60 * 60:
                # if now_time - file_time > 0:
                    plans = sorted(self.plans, key=itemgetter('duration'))
                else:
                    with open('stuty_plans.json', 'r') as fp:
                        plans = json.load(fp)
                new_plans = [i for i in plans if i.get('period') and i.get('period') != i.get('completed_period')]
    
                while True:
                    for i, course in enumerate(new_plans):
                        logging.info(course)
                        course_id = course.get('id')
                        plan_id = course.get('plan_id')
                        if not course.get('is_learning'):
                            r = self._add(plan_id, course_id)
                            if not r.get('study_plans'):
                                continue
                            logging.info('Add: {} {}'.format(course_id, plan_id))
                        for ware in course.get('coursewares'):
                            if ware.get('finish'):
                                logging.info('Finish:\t{}'.format(ware.get('title')))
                                continue
                            ware_id = ware.get('id')
                            if not self._study(ware_id):
                                continue
                            self.user_study(course_id, plan_id, ware_id, course, ware)
                        new_plans.pop(i)
            except json.decoder.JSONDecodeError:
                return
            except Exception as e:
                logging.error(e)

    @property
    def _(self):
        return int((time.time() +1) * 1000)


def main():
    logging.basicConfig(filename='log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    qwschool = QWschool()
    qwschool.always_study()


if __name__ == '__main__':
    main()
