from app.modules.gamification.schemas import AchievementDef, QuestDef, QuestEvent, QuestFrequency, AchievementType
from app.modules.quiz.schemas import QuizDifficulty


QUESTS: list[QuestDef] = [
    # daily
    {
        "id": "daily_login",
        "title": "Login Harian",
        "description": "Masuk ke aplikasi untuk memulai harimu",
        "event": QuestEvent.USER_LOGIN,
        "target": 1,
        "difficulty": QuizDifficulty.EASY,
        "frequency": QuestFrequency.DAILY,
        "xp_reward": 50,
    },
    {
        "id": "daily_stay_1hour",
        "title": "Fokus belajar selama 1 jam",
        "description": "Tetap di apliksi selama 1 jam",
        "event": QuestEvent.STAY_1_HOUR,
        "target": 1,
        "difficulty": QuizDifficulty.MEDIUM,
        "frequency": QuestFrequency.DAILY,
        "xp_reward": 50,
    },
    {
        "id": "daily_complete_3_task",
        "title": "Selesaikan 3 Tugas",
        "description": "Tandai 3 tugas sebagai selesai di Target dan Tugas",
        "event": QuestEvent.COMPLETE_TASK,
        "target": 3,
        "difficulty": QuizDifficulty.HARD,
        "frequency": QuestFrequency.DAILY,
        "xp_reward": 150,
    },

    # weekly
    {
        "id": "weekly_stay_10hour",
        "title": "Produktif Mingguan",
        "description": "Total 10 jam belajar minggu ini",
        "event": QuestEvent.STAY_10_MIN,
        "target": 60,
        "difficulty": QuizDifficulty.HARD,
        "frequency": QuestFrequency.WEEKLY,
        "xp_reward": 150,
    },
    {
        "id": "weekly_receive_5_like",
        "title": "Kontribusi forum",
        "description": "Dapatkan 5 like dalam forum yang kamu post",
        "event": QuestEvent.RECEIVE_LIKE,
        "target": 5,
        "difficulty": QuizDifficulty.EASY,
        "frequency": QuestFrequency.WEEKLY,
        "xp_reward": 50,
    },
]

ACHIEVEMENTS: list[AchievementDef] = [
    {
        "id": "completed_first_quest",
        "title": "First Step",
        "description": "Selesaikan quest pertama",
        "event": QuestEvent.COMPLETE_QUEST,
        "type": AchievementType.QUEST,
        "target": 1,
        "difficulty": QuizDifficulty.EASY,
        "xp_reward": 100,
    }
]